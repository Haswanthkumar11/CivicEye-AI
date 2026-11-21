# CivicEye AI – Master Project Plan

**Project Name:** CivicEye AI  
**Tagline:** Report it. Understand it. Resolve it. Track it.  
**Track:** Track 1 – Civic Pulse, Digital Governance & Public Information  
**Problem Statement:** Transparent Civic Grievance & Infrastructure Triage System  
**Version:** 1.1.0  
**Status:** In Progress (Phase 2 Completed, Phase 3 Next)  

---

## 1. Executive Summary & Architecture Overview

CivicEye AI is a multimodal AI-powered civic intelligence platform engineered to bridge the gap between unstructured citizen grievance reporting and structured, transparent, and actionable civic administration. The platform transforms photographs, videos, voice notes (Telugu and English), and text descriptions into structured issues, deterministically scores severity and public safety risk, routes tasks to municipal departments, identifies duplicate issues geographically, tracks civic hotspots, and offers an open transparency dashboard.

### Core Architecture Pillars

```
+---------------------------------------------------------------------------------+
|                                USER INTERFACES                                  |
|  +--------------------+   +------------------------+   +---------------------+  |
|  |   Citizen Portal   |   | Administrator Dashboard|   | Public Transparency |  |
|  | (Report, Audio, CV)|   | (Triage, Map, Assign)  |   | (Analytics, Hotspot)|  |
+--+---------+----------+---+-----------+------------+---+----------+-------------+
             |                          |                           |
             +--------------------------+---------------------------+
                                        | (REST APIs / Axios)
+---------------------------------------v-----------------------------------------+
|                          FASTAPI BACKEND SERVICE                                |
|  +---------------------------------------------------------------------------+  |
|  | API Router: /api/auth | /api/complaints | /api/ai | /api/dashboard        |  |
|  +---------------------------------------------------------------------------+  |
|  | Core Services:                                                            |  |
|  |   * Gemini Multimodal Pipeline (Text/Image/Audio reasoning)               |  |
|  |   * Local YOLO Road Damage Detector (OpenCV + Ultralytics)                |  |
|  |   * Local faster-whisper Speech Engine (Telugu + English int8 CPU/GPU)    |  |
|  |   * Priority & Severity Engine (Deterministic weighted formula)           |  |
|  |   * Spatial Duplicate & Hotspot Engine (PostGIS proximity + Embeddings)   |  |
|  |   * Department Router (Rules-based mapping with human override)           |  |
+--+---------------------------------------------------------------------------+--+
                                        |
+---------------------------------------v-----------------------------------------+
|                         DATA & STORAGE LAYER                                    |
|  +-------------------------------------+   +---------------------------------+  |
|  | PostgreSQL + PostGIS (Spatial DB)   |   | Supabase Storage / Local Media  |  |
|  | (Complaints, Users, Hotspots, Audit)|   | (Photos, Audio recordings)      |  |
+--+-------------------------------------+---+---------------------------------+--+
```

---

## 2. Technology Stack & Verification Matrix

| Component | Selected Technology | Licensing / Execution Mode | Justification / Notes |
| :--- | :--- | :--- | :--- |
| **Frontend Framework** | React 18 + Vite + TypeScript | MIT | High performance, type safety, fast HMR |
| **UI Styling** | Tailwind CSS + Lucide Icons | MIT | Clean, modern civic UI, responsive layouts |
| **Mapping** | Leaflet + OpenStreetMap | BSD-2-Clause / Open Data | Free, open-source geospatial visualization |
| **Analytics Charts** | Recharts | MIT | Composable SVG declarative civic charts |
| **Backend Framework**| FastAPI (Python 3.11) | MIT | High throughput, async support, native Pydantic schemas |
| **Database ORM** | SQLAlchemy 2.0 + PostGIS | MIT | Solid relational modeling with geospatial support |
| **Main AI Intelligence**| Google Gemini API | Cloud API via secure env | Multimodal understanding, translation, extraction |
| **Road Damage CV** | Local YOLO (Road Damage) | Free / Open Model (Local) | No paid CV APIs; runs on backend CPU/GPU |
| **Voice Recognition** | Local faster-whisper | MIT (Local Execution) | Free, multilingual (Telugu + English), int8 CPU |
| **Authentication** | JWT / Supabase Auth | Free / Open Standard | Role-based: Citizen vs Administrator |

---

## 3. Seven-Phase Implementation Roadmap

### Phase 1: Project Foundation (Current)
- [x] Inspect workspace and initialize clean directory structure.
- [x] Setup environment configuration templates (`.env.example`) and `.gitignore`.
- [x] Scaffold Vite + React + TypeScript frontend with Tailwind CSS and Lucide icons.
- [x] Scaffold FastAPI backend with modular architecture and CORS setup.
- [x] Implement system health check endpoint (`/api/health`).
- [x] Build comprehensive, professional Landing Page showcasing Citizen, Admin, and Public Transparency portals.
- [x] Verify frontend-to-backend communication.
- [x] Document project plan (`PROJECT_PLAN.md`) and development log (`DEVELOPMENT_LOG.md`).

### Phase 2: Database Schema & Authentication (Completed)
- [x] Define SQLAlchemy database models: `users`, `complaints`, `complaint_media`, `departments`, `ai_analysis_results`, `duplicate_groups`, `duplicate_relations`, `status_history`.
- [x] Configure PostGIS spatial coordinates and geospatial schemas with SQLite/Postgres dual-engine resilience.
- [x] Implement JWT authentication with role-based access control (Citizen vs Admin).
- [x] Seed default municipal departments and demo administrative credentials.
- [x] Connect frontend React AuthContext, AuthModal, and 1-Click Evaluation switcher to backend APIs.

### Phase 3: Citizen Complaint Management
- [ ] Build citizen complaint submission wizard with step-by-step progress.
- [ ] Implement photo, video, and audio recording upload interface.
- [ ] Implement interactive Leaflet location picker (GPS auto-detection + pin adjustment).
- [ ] Provide real-time pre-submission AI review card for the citizen.
- [ ] Implement citizen dashboard with live complaint tracking and status history.

### Phase 4: Multimodal AI Intelligence Pipeline
- [ ] Implement Gemini service for multilingual understanding, Telugu/English triage, and structured extraction.
- [ ] Implement modular local YOLO road damage detector with OpenCV preprocessing.
- [ ] Implement modular local faster-whisper speech transcription for Telugu and English audio notes.
- [ ] Implement deterministic priority scoring engine:  
  $$\text{Score} = 0.30 \times \text{Damage} + 0.30 \times \text{Risk} + 0.20 \times \text{Public Impact} + 0.20 \times \text{Location Sensitivity}$$
- [ ] Implement rules-based department routing with administrative override capabilities.

### Phase 5: Duplicate Detection & Civic Hotspot Intelligence
- [ ] Implement geospatial proximity indexing (PostGIS / Haversine distance thresholding).
- [ ] Implement text & semantic similarity comparison for nearby complaints.
- [ ] Implement administrator duplicate grouping interface (linking complaints without silent merges).
- [ ] Implement spatial clustering engine for recurring civic hotspots (potholes, garbage, water leaks).

### Phase 6: Admin Dashboard & Public Transparency Portal
- [ ] Build Administrative Command Center with priority queues, evidence viewer, and department dispatch.
- [ ] Implement status workflow: `SUBMITTED` -> `UNDER_REVIEW` -> `ASSIGNED` -> `IN_PROGRESS` -> `RESOLVED`.
- [ ] Implement resolution evidence capture (before/after inspection photos).
- [ ] Build Public Transparency Dashboard with anonymized civic metrics, resolution KPIs, and interactive city heatmaps.

### Phase 7: Integration, Testing & Final Documentation
- [ ] End-to-end testing of complete workflow from voice/photo report to administrative resolution.
- [ ] Validation of CPU/GPU resource usage and fallback handling for local AI models.
- [ ] Prepare demonstration fixtures (sample complaints across roads, sanitation, water, electrical).
- [ ] Complete comprehensive README and demonstration guide.

---

## 4. Architectural Rules & Compliance
1. **Never fabricate AI inferences:** If a model is not yet loaded or input is missing, the system gracefully degrades and flags for human review.
2. **Deterministic Severity:** AI suggests raw factors (0-100), but backend computes the official score mathematically.
3. **Transparent Governance:** Citizen identities and personal details are strictly scrubbed on the public dashboard.
4. **Local Models Only for CV & Speech:** No billable third-party vision or speech APIs; faster-whisper and YOLO execute locally on the backend.
