"""
CrowdPulse AI - Configuration
Loads environment variables and defines system-wide constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# ─── Groq LLM ───────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# ─── RTSP Camera ─────────────────────────────────────────────
RTSP_URL = os.getenv("RTSP_URL", "")

# ─── Weather (Open-Meteo) ────────────────────────────────────
STADIUM_LAT = float(os.getenv("STADIUM_LAT", "19.0448"))
STADIUM_LON = float(os.getenv("STADIUM_LON", "72.8258"))
WEATHER_CACHE_SECONDS = 300  # Cache weather for 5 minutes

# ─── Server ──────────────────────────────────────────────────
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# ─── Processing Intervals ────────────────────────────────────
YOLO_INFERENCE_INTERVAL = 2.0      # seconds between YOLO frames
AGENT_ORCHESTRATION_INTERVAL = 10.0  # seconds between full agent runs
TICKET_SCAN_INTERVAL = 0.5          # seconds between QR scan attempts

# ─── Crowd Thresholds ────────────────────────────────────────
DENSITY_THRESHOLDS = {
    "very_low": 0.5,    # people per sq meter
    "low": 1.5,
    "medium": 3.0,
    "high": 6.0,
    # anything above 6.0 = "very_high"
}

RISK_LEVELS = {
    "low": {"color": "#22c55e", "label": "Low"},
    "medium": {"color": "#f59e0b", "label": "Medium"},
    "high": {"color": "#f97316", "label": "High"},
    "critical": {"color": "#ef4444", "label": "Critical"},
}

# ─── Gate Capacities (persons/minute) ────────────────────────
GATE_CAPACITIES = {
    "Gate 1": 120,
    "Gate 2": 150,
    "Gate 3": 120,
    "Gate 4": 100,
    "Gate 5": 100,
}

# ─── YOLO ─────────────────────────────────────────────────────
YOLO_MODEL_NAME = "yolov8n.pt"
YOLO_CONFIDENCE_THRESHOLD = 0.4
PERSON_CLASS_ID = 0  # COCO class 0 = person
