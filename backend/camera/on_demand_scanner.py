import cv2
import logging
import numpy as np
import base64
from ultralytics import YOLO

logger = logging.getLogger("crowdpulse")

_model = None

def get_yolo_model():
    global _model
    if _model is None:
        logger.info("Loading YOLOv8n for on-demand scanner...")
        _model = YOLO("yolov8n.pt")
    return _model

def scan_image_data(image_data: bytes):
    """
    Runs YOLO person detection on raw image bytes.
    Returns (person_count, annotated_base64_string)
    """
    model = get_yolo_model()
    
    # Convert bytes to numpy array then to cv2 image
    nparr = np.frombuffer(image_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if frame is None:
        logger.error("Failed to decode image data")
        return 0, ""

    # Run inference
    results = model(frame, classes=[0], verbose=False)
    
    person_count = 0
    if len(results) > 0:
        person_count = len(results[0].boxes)
        # Draw bounding boxes
        annotated_frame = results[0].plot()
    else:
        annotated_frame = frame
        
    logger.info(f"On-demand scan detected {person_count} people.")
    
    # Encode back to base64 to send to frontend
    _, buffer = cv2.imencode('.jpg', annotated_frame)
    b64_str = base64.b64encode(buffer).decode('utf-8')
    
    return person_count, b64_str
