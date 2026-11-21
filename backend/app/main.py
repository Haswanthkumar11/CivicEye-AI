import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.api_v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown events"""
    # Ensure media directory exists
    os.makedirs(settings.MEDIA_UPLOAD_DIR, exist_ok=True)
    os.makedirs("models/weights", exist_ok=True)
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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Direct /api/health alias for convenience
from app.api.endpoints.health import health_check
app.add_api_route("/api/health", health_check, methods=["GET"], tags=["Health & Diagnostics"])
