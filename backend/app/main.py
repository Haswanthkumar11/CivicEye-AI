import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.api_v1 import api_router
from app.db.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown events"""
    # Ensure media directory exists
    os.makedirs(settings.MEDIA_UPLOAD_DIR, exist_ok=True)
    os.makedirs("models/weights", exist_ok=True)
    
    # Initialize and seed database tables
    try:
        init_db()
        print("📦 Database models and seed data verified.")
    except Exception as e:
        print(f"⚠️ Warning during DB startup init: {e}")
        
    print(f"🚀 {settings.PROJECT_NAME} v{settings.VERSION} initialized in {settings.ENVIRONMENT} mode.")
    yield
    print(f"🛑 {settings.PROJECT_NAME} backend shutting down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Multimodal AI-Powered Civic Intelligence Platform – Transparent Civic Grievance & Infrastructure Triage System",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"^https:\/\/.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    """Applies defensive security headers to prevent MIME sniffing, clickjacking, and XSS framing"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Dynamic and fallback media serving with Supabase Storage re-hydration
from fastapi import HTTPException
from fastapi.responses import FileResponse
from app.services.media_storage import media_storage_service

@app.get("/uploads/{filename}", tags=["Media"])
async def get_uploaded_media(filename: str):
    """
    Serves uploaded complaint media with fallback re-hydration from Supabase Storage
    to survive ephemeral container restarts.
    """
    safe_name = os.path.basename(filename)
    if ".." in safe_name or "/" in safe_name or "\\" in safe_name:
        raise HTTPException(status_code=400, detail="Invalid filename")

    local_file = media_storage_service.ensure_local_copy(safe_name)
    if local_file and os.path.isfile(local_file):
        return FileResponse(local_file)

    raise HTTPException(status_code=404, detail="Media file not found")

# Ensure upload directory exists before static mounting
os.makedirs(settings.MEDIA_UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.MEDIA_UPLOAD_DIR), name="uploads")

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "tagline": "Report it. Understand it. Resolve it. Track it.",
        "track": "Track 1 – Civic Pulse, Digital Governance & Public Information",
        "version": settings.VERSION,
        "status": "operational",
        "documentation": "/docs",
        "health": "/api/health",
    }


# Include V1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Aliases for direct /api/... paths
from app.api.endpoints.health import health_check
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.complaints import router as complaints_router
from app.api.endpoints.ai import router as ai_router

app.add_api_route("/health", health_check, methods=["GET"], tags=["Health & Diagnostics"])
app.add_api_route("/api/health", health_check, methods=["GET"], tags=["Health & Diagnostics"])
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication & User Management"])
app.include_router(complaints_router, prefix="/api/complaints", tags=["Complaints & Grievances"])
app.include_router(ai_router, prefix="/api/ai", tags=["AI Grievance Intelligence"])
