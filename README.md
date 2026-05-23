# CrowdPulse AI — Stadium Command Center

AI-powered real-time crowd management system for cricket stadiums with YOLOv8 people detection.

## Features
- 🏟️ Interactive stadium heatmap with real-time crowd density
- 🎥 Live video feed with YOLOv8 person detection & tracking
- 🤖 AI agent orchestration (crowd analysis, safety, weather)
- 📊 Real-time WebSocket updates via Socket.IO

## Local Setup

```bash
# 1. Clone
git clone https://github.com/05rahulbhardwaj/gc_apl_grandfinale.git
cd gc_apl_grandfinale

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 4. Add video files (not in repo due to size)
# Place People_entering_stadium.mp4 and food_court.mp4 in project root

# 5. Run
python backend/main.py
```

Open http://localhost:8000

## Docker

```bash
docker build -t crowdpulse-ai .
docker run -p 8000:8000 --env-file .env crowdpulse-ai
```

## Tech Stack
- **Backend**: FastAPI + Socket.IO + Uvicorn
- **AI/ML**: YOLOv8n (Ultralytics) + BoT-SORT tracker
- **Frontend**: Vanilla HTML/CSS/JS with Canvas
- **LLM**: Groq (Llama 3.3 70B)
