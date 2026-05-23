import json
import os
import threading
from pathlib import Path

# Path to the JSON file where detections are saved
DATA_DIR = Path("d:/final_h/backend/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DETECTIONS_FILE = DATA_DIR / "detections.json"

_file_lock = threading.Lock()

def _init_file():
    if not DETECTIONS_FILE.exists():
        with open(DETECTIONS_FILE, "w") as f:
            json.dump({}, f)

def get_all_detections() -> dict:
    """Reads all detection counts from the JSON file."""
    with _file_lock:
        _init_file()
        try:
            with open(DETECTIONS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}

def get_detection(zone_id: str) -> int:
    """Gets the count for a specific zone."""
    data = get_all_detections()
    return data.get(zone_id, 0)

def save_detection(zone_id: str, count: int):
    """Saves the count for a specific zone to the JSON file."""
    with _file_lock:
        _init_file()
        try:
            with open(DETECTIONS_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            data = {}
        
        data[zone_id] = count
        
        with open(DETECTIONS_FILE, "w") as f:
            json.dump(data, f, indent=4)
