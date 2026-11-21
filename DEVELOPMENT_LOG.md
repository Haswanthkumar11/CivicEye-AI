# CivicEye AI – Development Log

All implementation milestones, technical decisions, tests, and task states are systematically tracked here.

---

## Log Entry: 2026-11-21 – Phase 2 Database Architecture & Authentication Completed & Verified

### Status: Phase 2 Completed & Verified

### Completed Tasks
1. **Relational Database Architecture (`backend/app/models/`):**
   - Implemented normalized SQLAlchemy 2.0 models for all core platform entities:
     - `User` (`users`): UUID primary key, indexed unique email, bcrypt hash, full name, phone number, role (`citizen`, `admin`, `department_officer`), active state, timestamps.
     - `Department` (`departments`): UUID, unique code, name, description, contact email, active state.
     - `Complaint` (`complaints`): UUID, tracking ID (`CVE-...`), foreign keys to citizen, department, duplicate group, severity enum + float score, risk level, status enum, spatial coordinates (`latitude`, `longitude`).
     - `ComplaintMedia` (`complaint_media`): UUID, foreign key to complaint, media type (`IMAGE`, `VIDEO`, `AUDIO`), file URL, file path, mime type, size.
     - `Location` (`locations`): UUID, complaint link, latitude, longitude, address, landmark, ward, city, postal code.
     - `Assignment` (`assignments`): UUID, complaint, department, assigned by, assigned to, notes, timestamps, due date.
     - `ComplaintStatusHistory` (`complaint_status_history`): Audit trail of status transitions with actor ID and notes.
     - `AIAnalysisResult` (`ai_analysis_results`): UUID, complaint, language detected, transcript, YOLO detections JSON, Gemini analysis JSON, factor scores, calculated severity score.
     - `ResolutionEvidence` (`resolution_evidence`): Inspection notes, verified by officer ID, resolution evidence photo URL.
     - `Notification` (`notifications`): Citizen/admin real-time in-app alerts.
     - `DuplicateGroup` & `DuplicateRelation`: Duplicate tracking with similarity scores, match modalities (GEO, TEXT, IMAGE, COMPOSITE), and confirmation workflows.

2. **Dual-Engine Database Resilience (`backend/app/core/database.py`):**
   - Configured SQLAlchemy engine with automated connection pooling and timeout checks.
   - When PostgreSQL/PostGIS is running, connects natively via `psycopg` driver.
   - When running in local development or test without an active PostgreSQL service, gracefully falls back to local SQLite (`civiceye_dev.db`) with zero crashes.

3. **Database Seeding (`backend/app/db/init_db.py`):**
   - Auto-creates all tables on startup.
   - Pre-seeds 6 official municipal departments:
     - Municipal Roads & Infrastructure (`ROADS`)
     - Water Supply & Sewerage Board (`WATER`)
     - Solid Waste Management & Sanitation (`SANITATION`)
     - Storm Water & Surface Drainage (`DRAINAGE`)
     - Electricity & Public Lighting (`ELECTRICAL`)
     - Public Infrastructure & Parks (`PUBLIC_INFRA`)
   - Pre-seeds test credentials:
     - Demo Citizen: `citizen@civiceye.gov` / `Citizen@123`
     - Demo Administrator: `admin@civiceye.gov` / `Admin@123`

4. **Security & Role-Based Access Control (`backend/app/core/security.py`):**
   - Implemented direct `bcrypt` password hashing with salt generation (72-byte safe, eliminating passlib wrap bug).
   - JWT access token encoding/decoding with HMAC-SHA256 (`HS256`) and configurable expiration.
   - FastAPI dependencies: `get_current_user`, `require_admin`, and `require_citizen`.

5. **Authentication Endpoints (`backend/app/api/endpoints/auth.py`):**
   - `POST /api/auth/register` (also `/api/v1/auth/register`): User registration with email validation and immediate token issuance.
   - `POST /api/auth/login` (also `/api/v1/auth/login`): Password verification and JWT token return.
   - `GET /api/auth/me` (also `/api/v1/auth/me`): Protected profile endpoint returning authenticated user claims.
   - `POST /api/auth/demo-login` (also `/api/v1/auth/demo-login`): 1-click evaluation login for evaluators.

6. **Frontend Authentication System:**
   - Implemented `frontend/src/context/AuthContext.tsx` managing user session, JWT storage in `localStorage`, and token injection via Axios interceptor.
   - Implemented `frontend/src/components/auth/AuthModal.tsx` with Sign In, Citizen Registration, and 1-Click Demo Evaluation login.
   - Updated `Navbar.tsx` with authenticated user profile, role pill, and logout trigger.
   - Added 1-Click Persona Evaluator Quick Switcher to `LandingPage.tsx`.

---

### Verification and Tests Performed
- **Automated Pytest Suite:** `pytest tests/ -v` -> **9 PASSED (100%)**
  - `test_seed_demo_accounts_exist` PASSED
  - `test_user_registration` PASSED
  - `test_duplicate_registration_rejected` PASSED
  - `test_invalid_login_rejected` PASSED
  - `test_get_me_authenticated` PASSED
  - `test_demo_login_endpoints` PASSED
  - `test_root_endpoint` PASSED
  - `test_health_endpoint` PASSED
  - `test_v1_health_endpoint` PASSED
- **Live HTTP Integration Test:** Tested live server on socket:
  - `POST /api/v1/auth/demo-login` returned 200 OK + valid JWT for Citizen and Admin.
  - `GET /api/v1/auth/me` validated token and returned profile claims.
  - `POST /api/auth/register` successfully created new accounts and issued tokens.
- **Frontend Build Test:** `npm run build` -> **0 TypeScript errors, bundle compiled in 6.72s**.

---

### Exact Next Implementation Phase
- **Phase 3 – Citizen Complaint Management:**
  - Build citizen grievance submission wizard with step-by-step progress.
  - Implement photo, video, and audio file upload interface.
  - Implement interactive Leaflet location picker (GPS auto-detection + pin adjustment).
  - Connect grievance submission form to `POST /api/complaints` and persist to database.
  - Implement citizen dashboard with active grievance tracking and step-by-step status timeline.

---

## Log Entry: 2026-11-21 – Phase 1 Foundation Verified
*(See previous entry for Phase 1 milestones)*
