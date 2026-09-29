# CityAI Traffic Intelligence Platform
### City-Wide AI Engine for Multi-Camera ANPR Trajectory Tracking, Vehicle Intelligence and Urban Traffic Analytics

[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-v4-38B2AC.svg)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 1. Central Problem & Innovation

> **Core Axiom:** *Do not blindly trust the registration plate.*

Traditional Automatic Number Plate Recognition (ANPR) systems rely solely on OCR text, making them vulnerable to cloned license plates, counterfeit tags, and visual misreads. 

**CityAI Traffic Intelligence** correlates multi-modal visual and spatiotemporal evidence across an urban camera network:
* License plate OCR & Character confidence
* Vehicle type classification (Sedan, SUV, Truck, Bus, Motorcycle)
* Approximate dominant body color (quantized in HSV/LAB space)
* Camera graph topology & physical road distance matrix
* Spatiotemporal transit time feasibility ($\Delta d / \Delta t$)
* Inferred travel speed vs speed limits ($v > 140\text{ km/h}$)
* Official Demo DMV / RTO Registry records

When the same plate appears on conflicting vehicle appearances (e.g. White Sedan on CAM01 vs Black SUV on CAM04) or exhibits impossible physical velocity, the system generates a **POSSIBLE DUPLICATE / CLONED PLATE** alert.

---

## 2. Human-In-The-Loop Workflow

CityAI is strictly an **evidence-support and intelligence platform**. It never declares guilt or automates punitive fines.

```
AI Computer Vision Ingestion
         ↓
Multi-Factor Correlation & Evidence Harvesting
         ↓
Anomaly Detection (Duplicate Plate / Impossible Travel)
         ↓
Human Verification Workflow (Review Side-by-Side Dossier)
         ↓
Authorized Case Investigation
         ↓
Official Resolution
```

### Approved Terminology
* `POSSIBLE DUPLICATE PLATE`
* `POTENTIAL VIOLATION`
* `REQUIRES VERIFICATION`
* `UNDER INVESTIGATION`
* `PROBABLE MATCH` / `UNCERTAIN MATCH`

---

## 3. System Architecture

```
cityai-traffic/
├── backend/
│   ├── app/
│   │   ├── api/             # REST endpoints (Cameras, Vehicles, Alerts, Cases, Analytics, Simulation)
│   │   ├── models/          # SQLAlchemy Models (Camera, Vehicle, Detection, Plate, Trajectory, Alert, Case, Registry)
│   │   ├── schemas/         # Pydantic validation schemas
│   │   ├── services/        # AI engines (ANPR, Re-ID, Duplicate Plate, Topology, Weather, Simulator)
│   │   ├── config.py        # Centralized settings & thresholds
│   │   ├── database.py      # SQLite / SQLAlchemy connection
│   │   └── main.py          # FastAPI application entrypoint
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/      # Tactical glassmorphic UI components & Evidence Modals
│   │   ├── pages/           # Command Center, Map, CCTV, Vehicle Intel, Cloned Studio, Alerts, Cases, Analytics, Registry, Simulator
│   │   ├── services/        # Frontend API client
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
│
├── tests/                   # Pytest suite (Topology, Re-ID, Duplicate Plate, API endpoints)
└── README.md
```

---

## 4. Quick Start & Execution

### Prerequisites
* Python 3.12+
* Node.js v18+ & npm

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
* Interactive API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
* Operations Command Center: [http://localhost:5173](http://localhost:5173)

---

## 5. Automated Unit Tests

Run the automated test suite verifying graph shortest paths, Re-ID multi-factor scoring, duplicate plate detection, and API endpoints:
```bash
python -m pytest tests -v
```

---

## 6. Evaluation Scenarios

Use the built-in **Scenario Controller** (`/simulation`) to trigger live evaluation scenarios:

1. **Scenario 1: Cloned Plate Conflict**
   * Plate `TN38AB1234` active on CAM01 (White Sedan) and CAM04 (Black SUV).
   * Generates a `POSSIBLE DUPLICATE / CLONED PLATE` alert.
2. **Scenario 2: Impossible Speed Violation**
   * Plate `KA05MB9912` transits 18 km in 10 seconds.
   * Generates an `IMPOSSIBLE TRAVEL` alert ($v > 150\text{ km/h}$).
3. **Scenario 3: Stolen DMV Hotlist Intercept**
   * Sighting of registered stolen plate `DL01CA1024` on CAM02.
4. **Scenario 4: Traffic Congestion Bottleneck**
   * Spawns multi-vehicle queue on CAM03 (Expressway).
5. **Environmental Weather Simulation**
   * Switch between `CLEAR`, `RAIN`, `NIGHT`, and `FOG` to test OCR confidence degradation and environmental logging.
