# CivicEye AI 👁️🏛️

> **"Report it. Understand it. Resolve it. Track it."**

**Hackathon Track:** Track 1 – Civic Pulse, Digital Governance & Public Information  
**Problem Statement:** Transparent Civic Grievance & Infrastructure Triage System  

CivicEye AI is a multimodal AI-powered civic intelligence platform that transforms unstructured citizen complaints into structured, prioritized, and actionable civic resolutions. Citizens can report infrastructure issues using photographs, videos, voice recordings (Telugu and English), and text descriptions.

---

## 🏛️ System Overview

The platform bridges citizen reports and administrative action across three interconnected interfaces:

1. **Citizen Portal:** Effortless grievance reporting with multimodal capture, automated category/department suggestions, pre-submission AI preview, and transparent tracking timeline.
2. **Administrator Dashboard:** Municipal triage command center with deterministic priority scoring (0–100), PostGIS spatial duplicate grouping, and field resolution verification.
3. **Public Transparency Dashboard:** Open civic metrics, department SLA performance, and PostGIS density heatmaps for chronic infrastructure hotspots.

```
                                  CIVIC MEDIA INPUTS
                    [ Photos / Video / Telugu & English Voice / GPS ]
                                         │
                                         ▼
                     ┌───────────────────────────────────────┐
                     │         FASTAPI BACKEND CORE          │
                     ├───────────────────────────────────────┤
                     │ 1. Local faster-whisper (Telugu/Eng)  │
                     │ 2. Local YOLO Road Damage Vision      │
                     │ 3. Gemini Multimodal Extraction       │
                     │ 4. Deterministic Severity Scoring     │
                     │ 5. Rules-Based Department Router      │
                     │ 6. PostGIS Spatial Cluster Engine     │
                     └───────────────────┬───────────────────┘
                                         │
             ┌───────────────────────────┼───────────────────────────┐
             ▼                           ▼                           ▼
     [ Citizen Portal ]       [ Admin Dashboard ]         [ Public Transparency ]
   - Multimodal Submit      - Priority Triage (0-100)   - Civic Hotspot Heatmaps
   - Pre-submission Preview - Spatial Duplicate Review  - Resolution SLA Trends
   - Step-by-step Tracking  - Evidence Verification     - Anonymized Open Data
```

---

## 📐 Deterministic Severity Formula

To eliminate black-box hallucinations, while AI estimates raw normalized attributes (0–100), the backend deterministically calculates the final severity score:

$$\text{Severity Score} = 0.30 \times \text{Damage} + 0.30 \times \text{Risk} + 0.20 \times \text{Public Impact} + 0.20 \times \text{Location Sensitivity}$$

### Priority Bands
- **0 – 30:** `LOW`
- **31 – 60:** `MEDIUM`
- **61 – 80:** `HIGH`
- **81 – 100:** `CRITICAL`

---

## 🚀 Quickstart Guide

### Prerequisites
- **Python 3.10+ / 3.11**
- **Node.js 18+ / 22+**
- **PostgreSQL 15+ with PostGIS extension** (or SQLite fallback for dev)

### 1. Backend Setup

```bash
# Navigate to backend
cd backend

# Create & activate virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
copy ..\.env.example .env

# Run FastAPI backend
python run.py
# Or with uvicorn directly:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend endpoints will be available at:
- **API Base:** `http://localhost:8000/api`
- **Health Check:** `http://localhost:8000/api/health`
- **Interactive Swagger Docs:** `http://localhost:8000/docs`

### 2. Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```

Frontend application will be available at:
- `http://localhost:5173`

---

## 🧪 Testing Backend Health

To verify backend communication and endpoints:

```bash
cd backend
venv\Scripts\pytest tests/test_health.py -v
```

---

## 🛡️ Security & Privacy Principles
- **No Hardcoded Keys:** Secrets and API keys are stored strictly in backend `.env` files and never exposed to the frontend.
- **Privacy First:** Citizen names, phone numbers, and private photos are strictly sanitized before appearing on the Public Transparency Dashboard.
- **Free Local Inference:** Vision (YOLO road damage) and Speech (faster-whisper) run locally without incurring third-party API costs.
