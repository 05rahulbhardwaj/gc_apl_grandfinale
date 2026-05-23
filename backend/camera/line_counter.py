import cv2
import logging
import asyncio
from typing import AsyncGenerator
from datetime import datetime

logger = logging.getLogger("crowdpulse")

# Try to import from on_demand_scanner to avoid reloading the model twice if possible,
# but we can also just use the global YOLO model.
from ultralytics import YOLO

# Each stream needs its own model instance because model.track(persist=True)
# stores internal tracker state (previous frame). Sharing a model between
# streams with different video resolutions causes the optical flow GMC to crash.
_line_model = None

def _get_line_model():
    global _line_model
    if _line_model is None:
        logger.info("Loading separate YOLOv8n for line_counter...")
        _line_model = YOLO("yolov8n.pt")
    return _line_model

# We will need to update the state.
from backend.main import state_lock, stadium_state, sio, _serialise_state
from backend.models import DensityLevel
from backend.utils.state_store import save_detection

from pathlib import Path as _Path
_PROJECT_ROOT = _Path(__file__).resolve().parent.parent.parent
VIDEO_PATH = str(_PROJECT_ROOT / "People_entering_stadium.mp4")

gate_counts = {}

async def generate_line_crossing_stream(zone_id: str) -> AsyncGenerator[bytes, None]:
    """Generator that processes the video, tracks line crossing, and yields JPEG frames for MJPEG streaming."""
    global gate_counts
    gate_counts[zone_id] = 0
    save_detection(zone_id, 0)
    model = _get_line_model()
    
    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        logger.error(f"Could not open video file: {VIDEO_PATH}")
        return

    # Define a horizontal line near the middle of the frame
    # We will determine the coordinates based on the first frame
    line_y = None
    
    # Store the previous y-coordinate for each tracked ID
    previous_y = {}
    
    total_entered = 0

    try:
        while True:
            success, frame = cap.read()
            if not success:
                # Video ended or error, we can either break or loop
                # Let's break for now
                break

            height, width = frame.shape[:2]
            
            # Run YOLO tracking on clean frame
            results = model.track(frame, persist=True, classes=[0], verbose=False)

            # Initialize line_y if not set (e.g. middle of the frame)
            if line_y is None:
                line_y = int(height * 0.6) # 60% down the screen
            
            # Draw the line
            cv2.line(frame, (0, line_y), (width, line_y), (0, 255, 200), 2)
            
            if results and len(results) > 0 and results[0].boxes is not None:
                boxes = results[0].boxes
                
                # Check if tracking IDs are available
                if boxes.id is not None:
                    track_ids = boxes.id.int().cpu().tolist()
                    xywh = boxes.xywh.cpu().tolist()
                    
                    for box, track_id in zip(xywh, track_ids):
                        x_c, y_c, w, h = box
                        
                        # Draw clean, subtle bounding box corner brackets instead of ugly thick boxes
                        x1 = int(x_c - w/2)
                        y1 = int(y_c - h/2)
                        x2 = int(x_c + w/2)
                        y2 = int(y_c + h/2)
                        
                        color = (0, 200, 255) # Cyan
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 1)

                        if track_id in previous_y:
                            prev_y = previous_y[track_id]
                            
                            # Check if crossed the line (any direction)
                            if (prev_y > line_y and y_c <= line_y) or (prev_y < line_y and y_c >= line_y):
                                total_entered += 1
                                gate_counts[zone_id] = total_entered
                                save_detection(zone_id, total_entered)
                                # Update backend state live
                                await update_gate_state(zone_id, total_entered)
                        
                        # Update previous position
                        previous_y[track_id] = y_c
            
            # Encode frame
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue

            # Yield frame for MJPEG response
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # Simulate real-time (~30 fps)
            await asyncio.sleep(0.03)

    finally:
        cap.release()
        logger.info(f"Video stream for {zone_id} ended. Total entered: {total_entered}")


async def update_gate_state(zone_id: str, new_count: int):
    """
    Updates the global state and broadcasts via WebSocket.
    """
    if new_count <= 2:
        new_density = DensityLevel.LOW
    elif new_count <= 5:
        new_density = DensityLevel.MEDIUM
    elif new_count <= 10:
        new_density = DensityLevel.HIGH
    else:
        new_density = DensityLevel.VERY_HIGH

    updated = False
    with state_lock:
        for z in stadium_state.zones:
            if z.zone_id == zone_id:
                z.person_count = new_count
                z.density_level = new_density
                z.last_updated = datetime.now()
                updated = True
                break

    if updated:
        await sio.emit("state_update", _serialise_state())
    
    # Emit specific event for the video overlay
    await sio.emit("gate_count_update", {"zone_id": zone_id, "count": new_count})
