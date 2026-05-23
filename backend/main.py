"""
CrowdPulse AI - Main Application
FastAPI server with Socket.IO, MJPEG camera feeds, agent orchestration,
and real-time stadium state management.
"""

import sys
from pathlib import Path as _Path
# Ensure project root is on sys.path so `backend.*` imports resolve
_project_root = str(_Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import asyncio
import logging
import threading
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
import socketio
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.config import (
    HOST,
    PORT,
    RTSP_URL,
    AGENT_ORCHESTRATION_INTERVAL,
)
from backend.models import (
    StadiumState,
    ActionPlan,
    ActionItem,
    ActionType,
    Alert,
    AlertType,
    RiskLevel,
    ZoneStatus,
    GateData,
    WeatherData,
    DensityLevel,
)
from backend.camera.people_counter import PeopleCounter
from backend.camera.ticket_scanner import TicketScanner
from backend.services.weather_service import WeatherService
from backend.agents.orchestrator import AgentOrchestrator
from backend.utils.stadium_config import STADIUM_ZONES
from backend.utils.state_store import get_all_detections, save_detection

# ─── Logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger("crowdpulse")

# ─── Socket.IO (async mode for FastAPI) ──────────────────────
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

# ─── Global state ─────────────────────────────────────────────
stadium_state = StadiumState()
state_lock = threading.Lock()

# ─── Global service instances ─────────────────────────────────
people_counter: Optional[PeopleCounter] = None
ticket_scanner: Optional[TicketScanner] = None
weather_service = WeatherService()
orchestrator = AgentOrchestrator()

# ─── Background task handles ─────────────────────────────────
_orchestration_task: Optional[asyncio.Task] = None
_weather_task: Optional[asyncio.Task] = None
_scenario_task: Optional[asyncio.Task] = None
_scenario_running = False


# ─── Request body models ─────────────────────────────────────
class RtspBody(BaseModel):
    url: str


# ─── Lifespan ─────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    global people_counter, ticket_scanner
    global _orchestration_task, _weather_task

    logger.info("🏟️  CrowdPulse AI starting …")

    # 1. Initialize real state so zones exist immediately before analysis
    initial_zones, initial_gates = _build_real_data()
    
    with state_lock:
        stadium_state.zones = initial_zones
        stadium_state.gates = initial_gates

    # Start RTSP people counter (if URL configured)
    if RTSP_URL:
        people_counter = PeopleCounter(RTSP_URL)
        try:
            people_counter.start()
        except Exception as exc:
            logger.warning("RTSP camera unavailable: %s — using mock data", exc)
            people_counter = None

    # Start ticket scanner (webcam)
    # ticket_scanner = TicketScanner(camera_index=0)
    # try:
    #     ticket_scanner.start()
    # except Exception:
    #     logger.warning("Webcam unavailable — ticket scanner disabled")
    #     ticket_scanner = None

    # Preload ONE YOLO model instance for on-demand scans.
    # Line counter and area counter models will lazy-load on first use
    # to keep startup time fast for Cloud Run.
    from backend.camera.on_demand_scanner import get_yolo_model
    logger.info("Preloading YOLOv8 model...")
    get_yolo_model()
    logger.info("YOLOv8 model loaded and ready.")

    # Kick off async background loops
    # _orchestration_task = asyncio.create_task(_orchestration_loop()) # Disabled per user request
    _weather_task = asyncio.create_task(_weather_loop())

    yield  # ── app is running ──

    # Shutdown
    logger.info("🛑  CrowdPulse AI shutting down …")
    if people_counter:
        people_counter.stop()
    if ticket_scanner:
        ticket_scanner.stop()
    for task in (_weather_task, _scenario_task):
        if task and not task.done():
            task.cancel()


# ─── FastAPI app ──────────────────────────────────────────────
app = FastAPI(
    title="CrowdPulse AI",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Wrap with Socket.IO ASGI app
sio_app = socketio.ASGIApp(sio, other_asgi_app=app, socketio_path="/ws/socket.io")


# ─── Socket.IO events ────────────────────────────────────────

@sio.event
async def connect(sid, environ):
    logger.info("Socket.IO client connected: %s", sid)
    await sio.emit("state_update", _serialise_state(), room=sid)


@sio.event
async def disconnect(sid):
    logger.info("Socket.IO client disconnected: %s", sid)


# ─── REST API endpoints ──────────────────────────────────────

@app.get("/api/status")
async def get_status():
    """Return the full stadium state snapshot."""
    return _serialise_state()


@app.get("/api/zones")
async def get_zones():
    """Return current zone statuses."""
    with state_lock:
        return [z.model_dump(mode="json") for z in stadium_state.zones]


@app.post("/api/actions/{action_type}")
async def trigger_action(action_type: str):
    """Manually trigger an action (notify_fans, dispatch_staff, etc.)."""
    try:
        at = ActionType(action_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown action type: {action_type}")

    confirmation = {
        "action_type": at.value,
        "status": "executed",
        "message": f"Action '{at.value}' has been triggered.",
        "timestamp": datetime.now().isoformat(),
    }

    # Mark matching actions as executed in the current plan
    with state_lock:
        for item in stadium_state.action_plan.actions:
            if item.action_type == at and not item.is_executed:
                item.is_executed = True
                item.executed_at = datetime.now()

    await sio.emit("action_executed", confirmation)
    logger.info("Action executed: %s", at.value)
    return confirmation


@app.post("/api/rtsp")
async def set_rtsp(body: RtspBody):
    """Set a new RTSP URL and (re)start the people counter."""
    global people_counter

    if people_counter:
        people_counter.stop()

    people_counter = PeopleCounter(body.url)
    try:
        people_counter.start()
    except Exception as exc:
        logger.error("Failed to start RTSP stream: %s", exc)
        people_counter = None
        raise HTTPException(status_code=500, detail=str(exc))

    return {"status": "ok", "url": body.url}


@app.get("/api/camera/feed")
async def camera_feed():
    """MJPEG stream of the RTSP camera with YOLO bounding boxes."""
    if people_counter is None or not people_counter.is_running:
        raise HTTPException(status_code=503, detail="RTSP camera not connected")
    return StreamingResponse(
        _generate_mjpeg(people_counter.get_annotated_frame),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/api/camera/ticket-feed")
async def ticket_feed():
    """MJPEG stream of the ticket scanner webcam."""
    if ticket_scanner is None or not ticket_scanner.is_running:
        raise HTTPException(status_code=503, detail="Webcam not available")
    return StreamingResponse(
        _generate_mjpeg(ticket_scanner.get_frame),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


from fastapi import File, UploadFile

@app.post("/api/zone-scan/{zone_id}")
async def scan_zone(zone_id: str, file: UploadFile = File(...)):
    """On-demand scan using uploaded image from the frontend browser camera."""
    from backend.camera.on_demand_scanner import scan_image_data
    from backend.models import DensityLevel

    # 1. Read uploaded image data
    image_data = await file.read()

    # 2. Run YOLO on the image data
    person_count, annotated_b64 = scan_image_data(image_data)

    # 3. Map count to density
    if person_count <= 1:
        new_density = DensityLevel.LOW
    elif person_count <= 3:
        new_density = DensityLevel.MEDIUM
    elif person_count <= 5:
        new_density = DensityLevel.HIGH
    else:
        new_density = DensityLevel.VERY_HIGH

    # 4. Update state
    updated = False
    with state_lock:
        for z in stadium_state.zones:
            if z.zone_id == zone_id:
                z.person_count = person_count # Set directly instead of add for demo purposes
                save_detection(zone_id, person_count)
                z.density_level = new_density
                z.last_updated = datetime.now()
                updated = True
                break

    if not updated:
        raise HTTPException(status_code=404, detail=f"Zone {zone_id} not found")

    # 5. Broadcast the update instantly so the dots turn red
    await sio.emit("state_update", _serialise_state())
    
    return {
        "status": "success",
        "zone_id": zone_id,
        "person_count_in_frame": person_count,
        "new_density": new_density.value,
        "annotated_image": f"data:image/jpeg;base64,{annotated_b64}"
    }

from fastapi.responses import StreamingResponse

@app.get("/api/stream-gate/{zone_id}")
async def stream_gate_video(zone_id: str):
    """Returns a live MJPEG stream. Routes to line crossing for gates, area tracking for food court."""
    if zone_id == "food_court":
        from backend.camera.area_counter import generate_area_tracking_stream
        return StreamingResponse(
            generate_area_tracking_stream(zone_id),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )
    else:
        from backend.camera.line_counter import generate_line_crossing_stream
        return StreamingResponse(
            generate_line_crossing_stream(zone_id),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )

@app.get("/api/gate-count/{zone_id}")
async def get_gate_count(zone_id: str):
    """Returns the current count for a specific stream."""
    try:
        if zone_id == "food_court":
            from backend.camera.area_counter import gate_counts
        else:
            from backend.camera.line_counter import gate_counts
        return {"zone_id": zone_id, "count": gate_counts.get(zone_id, 0)}
    except ImportError:
        return {"zone_id": zone_id, "count": 0}

@app.post("/api/agents/analyze")
async def run_manual_analysis():
    """Manually trigger the orchestration cycle to run agents."""
    try:
        await _run_single_orchestration()
        return {"status": "success", "message": "Analysis complete"}
    except Exception as e:
        logger.error(f"Manual analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scenario/start")
async def scenario_start():
    """Scenario auto-advance disabled because mock data was removed."""
    return {"status": "disabled", "total_phases": 0}


@app.post("/api/scenario/reset")
async def scenario_reset():
    """Scenario reset disabled because mock data was removed."""
    return {"status": "disabled", "phase": 0}


# ─── MJPEG generator ─────────────────────────────────────────

async def _generate_mjpeg(get_frame_fn):
    """Yield JPEG frames for an MJPEG StreamingResponse."""
    while True:
        frame = get_frame_fn()
        if frame is None:
            await asyncio.sleep(0.1)
            continue
        _, buffer = cv2.imencode(".jpg", frame)
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + buffer.tobytes()
            + b"\r\n"
        )
        await asyncio.sleep(0.05)  # ~20 fps


# ─── Background loops ────────────────────────────────────────

async def _orchestration_loop():
    """Run agent orchestration every AGENT_ORCHESTRATION_INTERVAL seconds."""
    while True:
        try:
            await _run_single_orchestration()
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error("Orchestration error: %s", exc, exc_info=True)
        await asyncio.sleep(AGENT_ORCHESTRATION_INTERVAL)


async def _run_single_orchestration():
    """Gather data, run orchestrator, update state, emit via Socket.IO."""
    global stadium_state

    # 1. Gather real data
    zones, gates = _build_real_data()
    ticket_batch = [] # mock_data.get_ticket_scan_batch(5) removed

    # 2. Weather
    weather = weather_service.get_weather()

    # 3. YOLO count (if available)
    yolo_count = 0
    if people_counter and people_counter.is_running:
        yolo_count = people_counter.get_count()

    # 4. Ticket scanner info
    scan_rate = 0.0
    if ticket_scanner:
        scan_rate = float(ticket_scanner.total_scans) / max(1, 1)  # rough

    # 5. Build interim state for orchestrator input
    total_inside = sum(z.person_count for z in zones if z.zone_id.startswith(("north", "south", "east", "west")))
    total_outside = sum(z.person_count for z in zones if z.zone_id.startswith("gate"))

    with state_lock:
        stadium_state.zones = zones
        stadium_state.gates = gates
        stadium_state.weather = weather
        stadium_state.total_crowd_inside = total_inside + yolo_count
        stadium_state.total_crowd_outside = total_outside
        stadium_state.ticket_scans_per_min = scan_rate
        stadium_state.match_info["status"] = "Live (Real Data)"

    # 6. Run orchestrator (CPU-bound → run in executor)
    loop = asyncio.get_event_loop()
    with state_lock:
        snapshot = stadium_state.model_copy(deep=True)

    responses, action_plan = await loop.run_in_executor(
        None, orchestrator.run_cycle, snapshot
    )

    # 7. Generate alerts from agent responses
    alerts = _extract_alerts(responses)

    # 8. Update global state
    with state_lock:
        stadium_state.agent_responses = responses
        stadium_state.action_plan = action_plan
        stadium_state.alerts = alerts
        stadium_state.live_updates = [
            f"[{r.agent_name}] {r.summary}" for r in responses
        ]
        stadium_state.last_updated = datetime.now()

    # 9. Emit via Socket.IO
    state_json = _serialise_state()
    await sio.emit("state_update", state_json)

    for resp in responses:
        await sio.emit(
            "agent_message",
            resp.model_dump(mode="json"),
        )

    for alert in alerts:
        await sio.emit("alert", alert.model_dump(mode="json"))

    logger.info(
        "Cycle complete – risk=%s  safety=%d  zones=%d",
        action_plan.overall_risk.value,
        action_plan.safety_score,
        len(zones),
    )


async def _weather_loop():
    """Refresh weather every 5 minutes."""
    while True:
        try:
            w = weather_service.get_weather()
            with state_lock:
                stadium_state.weather = w
            logger.info("Weather updated: %s %.1f°C", w.weather_description, w.temperature)
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error("Weather loop error: %s", exc)
        await asyncio.sleep(300)


async def _scenario_loop():
    """Auto-advance demo scenario disabled."""
    pass


# ─── Helpers ──────────────────────────────────────────────────

def _build_real_data():
    detections = get_all_detections()
    zones = []
    gates = []
    for z in STADIUM_ZONES:
        count = detections.get(z["zone_id"], 0)
        density_val = count / max(z["area_sqm"], 1)
        if count <= 10: dl = DensityLevel.LOW
        elif count <= 50: dl = DensityLevel.MEDIUM
        elif count <= 100: dl = DensityLevel.HIGH
        else: dl = DensityLevel.VERY_HIGH
        
        zones.append(ZoneStatus(
            zone_id=z["zone_id"],
            zone_name=z["zone_name"],
            person_count=count,
            capacity=z["capacity"],
            density_level=dl,
            density_value=density_val,
            entry_rate=0.0,
            is_covered=z["is_covered"],
            last_updated=datetime.now()
        ))
        
        if z.get("type") == "gate" or z["zone_id"].startswith("gate"):
            cap = z.get("capacity", 120)
            gates.append(GateData(
                gate_id=z["zone_id"],
                gate_name=z["zone_name"],
                person_count=count,
                wait_time_minutes=round(count / 10.0, 1),
                throughput_per_minute=10.0,
                status="open",
                density_level=dl,
                last_updated=datetime.now()
            ))
    return zones, gates

def _serialise_state() -> dict:
    """Thread-safe serialisation of the global stadium state."""
    with state_lock:
        return stadium_state.model_dump(mode="json")


def _extract_alerts(responses: list) -> list[Alert]:
    """Turn high/critical agent responses into Alert objects."""
    alerts: list[Alert] = []
    for resp in responses:
        rl = resp.risk_level
        if isinstance(rl, str):
            try:
                rl = RiskLevel(rl)
            except ValueError:
                rl = RiskLevel.LOW

        if rl in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            alerts.append(
                Alert(
                    alert_id=str(uuid.uuid4()),
                    alert_type=AlertType.CONGESTION,
                    severity=rl,
                    title=f"{resp.agent_name} Alert",
                    description=resp.summary,
                    zone="",
                    timestamp=datetime.now(),
                    is_resolved=False,
                )
            )
    return alerts


# ─── Static files (frontend) ─────────────────────────────────
_frontend_dir = Path(__file__).parent.parent / "frontend"
if _frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")
else:
    logger.warning("Frontend directory not found at %s", _frontend_dir)


# ─── Entry point ──────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        sio_app,  # serve the Socket.IO-wrapped app
        host=HOST,
        port=PORT,
        log_level="info",
    )
