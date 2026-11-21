from fastapi import APIRouter
from app.api.endpoints import health, auth

api_router = APIRouter()

# Health and diagnostics
api_router.include_router(health.router, tags=["Health & Diagnostics"])

# Authentication & Users
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & User Management"])
