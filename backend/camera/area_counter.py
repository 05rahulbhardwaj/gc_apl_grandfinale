import cv2
import logging
import asyncio
from typing import AsyncGenerator
from datetime import datetime

logger = logging.getLogger("crowdpulse")

from ultralytics import YOLO

# Each stream needs its own model instance because model.track(persist=True)
# stores internal tracker state. Sharing causes optical flow crashes.
_area_model = None

def _get_area_model():
    global _area_model
    if _area_model is None:
        logger.info("Loading separate YOLOv8n for area_counter...")
        _area_model = YOLO("yolov8n.pt")
    return _area_model
from backend.main import state_lock, stadium_state, sio, _serialise_state
from backend.models import DensityLevel
from backend.utils.state_store import save_detection

from pathlib import Path as _Path
_PROJECT_ROOT = _Path(__file__).resolve().parent.parent.parent
FOOD_COURT_VIDEO = str(_PROJECT_ROOT / "food_court.mp4")

gate_counts = {}

async def generate_area_tracking_stream(zone_id: str) -> AsyncGenerator[bytes, None]:
    global gate_counts
    gate_counts[zone_id] = 0
    save_detection(zone_id, 0)
    
    model = _get_area_model()
    cap = cv2.VideoCapture(FOOD_COURT_VIDEO)
    
    if not cap.isOpened():
        logger.error(f"Could not open video file: {FOOD_COURT_VIDEO}")
        return

    try:
        while True:
            try:
                success, frame = cap.read()
                if not success:
                    break
                
                # Run YOLO tracking on clean frame
                results = model.track(frame, persist=True, classes=[0], verbose=False)
                current_count = 0
                
                if results and len(results) > 0 and results[0].boxes is not None:
                    boxes = results[0].boxes
                    
                    if boxes.id is not None:
                        track_ids = boxes.id.int().cpu().tolist()
                        xywh = boxes.xywh.cpu().tolist()
                        current_count = len(track_ids)
                        
                        for box, track_id in zip(xywh, track_ids):
                            x_c, y_c, w, h = box
                            x1 = int(x_c - w/2)
                            y1 = int(y_c - h/2)
                            x2 = int(x_c + w/2)
                            y2 = int(y_c + h/2)
                            
                            color = (50, 255, 50) # Green for area tracking
                            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    elif boxes.xywh is not None:
                        current_count = len(boxes.xywh)
                        for box in boxes.xywh.cpu().tolist():
                            x_c, y_c, w, h = box
                            x1 = int(x_c - w/2)
                            y1 = int(y_c - h/2)
                            x2 = int(x_c + w/2)
                            y2 = int(y_c + h/2)
                            color = (50, 255, 50)
                            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                
                # Draw total count overlay on the frame
                height, width = frame.shape[:2]
                label = f"People: {current_count}"
                cv2.putText(frame, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
                
                # Update state with current occupancy count
                gate_counts[zone_id] = current_count
                save_detection(zone_id, current_count)
                await update_area_state(zone_id, current_count)

                # Encode frame
                ret, buffer = cv2.imencode('.jpg', frame)
                if not ret:
                    continue

                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                # Simulate real-time (~30 fps)
                await asyncio.sleep(0.03)
            except Exception as loop_e:
                logger.error(f"Error in area tracking loop: {loop_e}")
                break

    finally:
        cap.release()
        logger.info(f"Video stream for {zone_id} ended. Final count: {gate_counts.get(zone_id, 0)}")

async def update_area_state(zone_id: str, new_count: int):
    """Updates the global state for an area and broadcasts via WebSocket."""
    if new_count <= 20:
        new_density = DensityLevel.LOW
    elif new_count <= 50:
        new_density = DensityLevel.MEDIUM
    elif new_count <= 100:
        new_density = DensityLevel.HIGH
    else:
        new_density = DensityLevel.VERY_HIGH

    updated = False
    with state_lock:
        for z in stadium_state.zones:
            if z.zone_id == zone_id:
                if z.person_count != new_count:
                    z.person_count = new_count
                    z.density_level = new_density
                    z.last_updated = datetime.now()
                    updated = True
                break

    if updated:
        await sio.emit("state_update", _serialise_state())
    
    # Emit specific event for the video overlay
    await sio.emit("gate_count_update", {"zone_id": zone_id, "count": new_count})
