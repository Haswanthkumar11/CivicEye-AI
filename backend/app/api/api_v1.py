from fastapi import APIRouter
from app.api.endpoints import health, auth, complaints

api_router = APIRouter()

# Health and diagnostics
api_router.include_router(health.router, tags=["Health & Diagnostics"])

# Authentication & Users
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & User Management"])

# Complaints & Citizen Grievances
api_router.include_router(complaints.router, prefix="/complaints", tags=["Complaints & Grievances"])
