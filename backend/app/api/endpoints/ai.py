from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.ai.schemas import (
    ComplaintAnalysisRequest,
    ComplaintAnalysisResponse,
)
from app.services.ai.ai_pipeline import AIPipeline
from app.services.ai.model_registry import ModelRegistry

router = APIRouter()
pipeline = AIPipeline()


@router.post(
    "/analyze-complaint",
    response_model=ComplaintAnalysisResponse,
    summary="Analyze Grievance via Multimodal AI Pipeline",
)
async def analyze_complaint(
    request: ComplaintAnalysisRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Analyzes civic grievance text using Gemini AI with deterministic fallback:
    - Extracts structured complaint attributes, damage, and public risk.
    - Computes deterministic explainable priority score (0-100).
    - Maps issue to responsible municipal department.
    Requires authenticated session.
    """
    analysis = await pipeline.analyze(request)
    return analysis


@router.get(
    "/status",
    summary="AI Intelligence Pipeline & Model Registry Diagnostic Status",
)
async def get_ai_status(
    current_user: User = Depends(get_current_user),
):
    """
    Returns AI pipeline configuration, Gemini availability status, and local model readiness.
    """
    status_data = ModelRegistry.get_status()
    status_data.update({
        "gemini_available": pipeline.gemini.is_available(),
        "gemini_model": pipeline.gemini.model_name,
        "ai_analysis_enabled": pipeline.gemini.enabled,
    })
    return status_data
