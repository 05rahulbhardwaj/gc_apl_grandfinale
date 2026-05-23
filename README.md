<div align="center">

# 🛡️ Eternal Crowd Sense AI

### AI-Powered Stadium Command Center

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/Groq-LLaMA_3.1-orange?logo=meta&logoColor=white)](https://groq.com)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-purple?logo=yolo&logoColor=white)](https://ultralytics.com)
[![GCP](https://img.shields.io/badge/GCP-Cloud_Run-red?logo=google-cloud&logoColor=white)](https://cloud.google.com/run)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

**Eternal Crowd Sense AI** is a real-time, AI-powered stadium crowd management system that combines **computer vision (YOLOv8)**, **multi-agent AI orchestration (Groq LLaMA 3.1)**, and a **premium dark-themed dashboard** to deliver intelligent crowd monitoring, safety scoring, and fan communication — all from a single command center.

[Live Demo](https://crowdpulse-ai-756566763557.asia-south1.run.app) • [Report Bug](https://github.com/05rahulbhardwaj/gc_apl_grandfinale/issues) • [Request Feature](https://github.com/05rahulbhardwaj/gc_apl_grandfinale/issues)

</div>

---

## 📸 Screenshots

### 🏟️ Full Dashboard — Stadium Map & Agent Reasoning Panel
![Dashboard with Stadium Heatmap and AI Agent Reasoning](screenshots/Screenshot%202026-05-23%20150154.png)

> The main dashboard showing the **live stadium heatmap** with particle-based crowd visualization across all gates and stands, alongside the **Agent Reasoning Panel** displaying real-time AI analysis from 6 specialized agents.

---

### 🗺️ Stadium Map & Live Heatmap (Close-up)
![Stadium Map Close-up](screenshots/Screenshot%202026-05-23%20150214.png)

> Interactive canvas-based stadium map with **color-coded density indicators** (green = low, orange = medium, red = high). Each gate, stand, and the food court area are labeled with live crowd counts.

---

### 📊 Live Statistics & Action Plan
![Live Stats Panel](screenshots/Screenshot%202026-05-23%20150203.png)

> Bottom row panels showing: **Safety Index** (AI-computed 0–100 score), **Live Situation** (total inside, outside queue, scans/min, wait time, security & volunteer counts), **Crowd Trend Chart** (60-minute rolling window), and **Action Plan** with one-click SMS broadcast.

---

### 📱 SMS Broadcast — Real Fan Notification
<div align="center">
<img src="screenshots/WhatsApp Image 2026-05-23 at 3.00.41 PM.jpeg" width="300" alt="SMS Notification">
</div>

> Real SMS received by a fan with personalized gate entry, exit, and seat information — sent directly from the dashboard via **Fast2SMS API**.

---

## ✨ Key Features

### 🤖 Multi-Agent AI System (6 Specialist Agents)
| Agent | Role | What It Does |
|-------|------|--------------|
| 🧑‍🤝‍🧑 **Crowd Monitor** | Density Analysis | Analyzes zone-wise crowd density, detects hotspots, predicts surges |
| 🎫 **Ticketing & Entry** | Gate Management | Monitors scan rates, detects duplicate/invalid tickets, optimizes gate throughput |
| 🗺️ **Route Planner** | Flow Optimization | Recommends rerouting when gates are congested, optimizes stand-gate assignments |
| 🌦️ **Weather Risk** | Environmental Safety | Assesses weather impact on crowd safety, triggers shelter protocols |
| 🚨 **Emergency Response** | Crisis Management | Evaluates multi-threat scenarios, recommends evacuation routes and staff dispatch |
| 📢 **Fan Communication** | Messaging | Generates context-aware messages for fans, volunteers, and security staff |

All agents run through a central **Orchestrator** that synthesizes a unified **Action Plan** with an AI-computed **Safety Score (0–100)**.

### 🎯 Real-Time Computer Vision
- **YOLOv8** person detection on live video feeds (RTSP or uploaded video)
- Automatic crowd counting across multiple zones
- Real-time density classification (Very Low → Very High)

### 🗺️ Interactive Stadium Heatmap
- Canvas-based particle visualization with **1000+ animated dots**
- Color-coded density per zone (green/orange/red)
- Gate labels, stand names, food court area
- Live WebSocket updates

### 📊 Live Dashboard Metrics
- **Safety Index**: AI-generated gauge (0–100) with trend indicator
- **Live Situation**: Total inside, outside queue, scans/min, wait time
- **Crowd Trend Chart**: 60-minute rolling area chart (Chart.js)
- **Agent Reasoning Panel**: Timestamped AI insights from all 6 agents

### 📱 SMS Broadcasting (Fast2SMS)
- Add unlimited contacts via Settings panel
- One-click broadcast: Entry gate, exit gate, and seat information
- Personalized messages: "Hi [Name], Your match entry is via Gate 1, exit via Gate 3. Seat: [Seat No]."

### 🥚 Easter Egg: "Who's Your Cricket Twin?"
- Hidden **Google** logo in the header (hover to reveal!)
- Opens webcam, captures your selfie
- Compares against celebrity cricketers (Bumrah, Dhoni, Kohli, Rohit Sharma, Sundar Pichai)
- Uses OpenCV face detection + histogram comparison
- Shows similarity scores with progress bars

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Vanilla JS)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ Stadium  │ │  Agent   │ │  Live    │ │  Action  │   │
│  │ Heatmap  │ │ Reasoning│ │  Stats   │ │   Plan   │   │
│  │ (Canvas) │ │  Panel   │ │ (Charts) │ │  (SMS)   │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│                    WebSocket (Socket.IO)                  │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                  Backend (FastAPI + Uvicorn)              │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │              Agent Orchestrator                   │    │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │    │
│  │  │ Crowd  │ │Ticket  │ │ Route  │ │Weather │   │    │
│  │  │Monitor │ │ Entry  │ │Planner │ │  Risk  │   │    │
│  │  └────────┘ └────────┘ └────────┘ └────────┘   │    │
│  │  ┌────────┐ ┌────────┐                          │    │
│  │  │Emergcy │ │Fan Comm│                          │    │
│  │  │Response│ │  Agent │                          │    │
│  │  └────────┘ └────────┘                          │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  YOLOv8      │  │  Groq API    │  │  Fast2SMS    │  │
│  │  (CV Model)  │  │  (LLaMA 3.1) │  │  (SMS API)   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- [Groq API Key](https://console.groq.com/) (free tier works)
- [Fast2SMS API Key](https://www.fast2sms.com/) (for SMS broadcasting)

### 1. Clone the Repository
```bash
git clone https://github.com/05rahulbhardwaj/gc_apl_grandfinale.git
cd gc_apl_grandfinale
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
HOST=0.0.0.0
PORT=8000
```

### 5. Run the Application
```bash
# Option 1: Using the batch file (Windows)
run.bat

# Option 2: Direct command
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

The dashboard will automatically open at `http://localhost:8000`.

---

## 📖 How to Use

### 1. 🗺️ Stadium Heatmap
The main view shows a real-time particle-based heatmap of the stadium. Each dot represents a person, and colors indicate density:
- 🟢 **Green** — Very Low / Low density
- 🟠 **Orange** — Medium density
- 🔴 **Red** — High / Very High density

### 2. 🤖 Run AI Analysis
Click the **"Get Analysis"** button in the Agent Reasoning Panel to trigger all 6 AI agents. Each agent analyzes its domain and provides:
- Risk level assessment
- Specific recommendations
- Timestamped reasoning visible in the panel

### 3. 📊 Monitor Live Stats
The bottom row provides at-a-glance metrics:
- **Safety Index**: Overall safety score (0–100) with color-coded gauge
- **Live Situation**: Real-time counts of people inside, outside, and staff
- **Crowd Trend**: Historical chart showing crowd movement over 60 minutes

### 4. 📱 Send SMS Broadcasts
1. Click the **⚙️ Settings** icon in the top-right
2. Add contacts with **Name**, **Mobile Number**, and **Seat Number**
3. Go to the **Action Plan** panel and click **"Broadcast"**
4. Each contact receives a personalized SMS with their gate and seat info

### 5. 📹 Connect Live Camera
Click the **"RTSP"** button to connect a live video feed (e.g., IP camera or RTSP stream). YOLOv8 will automatically detect and count people in real-time.

### 6. 🥚 Find Your Cricket Twin (Easter Egg!)
Look for the faintly visible **Google** text next to the settings icon. Click it to open the face match feature — take a selfie and discover which cricketer you resemble!

---

## 🗂️ Project Structure

```
eternal-crowd-sense-ai/
├── backend/
│   ├── agents/                    # 6 AI agents + orchestrator
│   │   ├── base_agent.py          # Base agent with Groq integration
│   │   ├── crowd_agent.py         # Crowd monitoring agent
│   │   ├── ticketing_agent.py     # Ticketing & entry agent
│   │   ├── route_agent.py         # Route planning agent
│   │   ├── weather_agent.py       # Weather risk agent
│   │   ├── emergency_agent.py     # Emergency response agent
│   │   ├── fan_comm_agent.py      # Fan communication agent
│   │   └── orchestrator.py        # Multi-agent orchestrator
│   ├── camera/
│   │   └── face_match.py          # Easter egg: celebrity face matching
│   ├── data/
│   │   └── detections.json        # YOLO detection data
│   ├── utils/
│   │   └── stadium_config.py      # Stadium layout configuration
│   ├── config.py                  # App configuration
│   ├── main.py                    # FastAPI application
│   └── models.py                  # Pydantic data models
├── frontend/
│   ├── css/
│   │   └── styles.css             # Premium dark theme CSS
│   ├── js/
│   │   ├── app.js                 # Main application logic
│   │   ├── live_panel.js          # Live stats & Chart.js
│   │   ├── stadium_map.js         # Canvas particle heatmap
│   │   ├── agents_panel.js        # Agent reasoning panel
│   │   ├── actions_panel.js       # Action plan panel
│   │   └── websocket.js           # Socket.IO client
│   ├── index.html                 # Main dashboard
│   └── face-match.html            # Easter egg page
├── celebrity_image/               # Celebrity images for face matching
├── screenshots/                   # App screenshots
├── Dockerfile                     # Docker configuration
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
└── README.md                      # This file
```

---

## ☁️ Deployment (Google Cloud Run)

```bash
gcloud run deploy eternal-crowd-sense \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --set-env-vars GROQ_API_KEY=your_key,GROQ_MODEL=llama-3.1-8b-instant,HOST=0.0.0.0 \
  --port 8080
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | HTML5, CSS3, Vanilla JavaScript, Chart.js, Socket.IO Client |
| **Backend** | Python, FastAPI, Uvicorn, Python-SocketIO |
| **AI/ML** | Groq (LLaMA 3.1 8B), YOLOv8 (Ultralytics), OpenCV |
| **SMS API** | Fast2SMS (Bulk SMS India) |
| **Deployment** | Docker, Google Cloud Run |
| **Real-time** | WebSocket (Socket.IO) |

---

## 👥 Team

Built with ❤️ for the **Google Cloud Platform Hackathon — Grand Finale**

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**⭐ Star this repo if you find it useful!**

Made with 🏏 for cricket fans everywhere

</div>
