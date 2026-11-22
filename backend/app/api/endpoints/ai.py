import os
import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, status, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.complaint import ComplaintMedia
from app.services.ai.schemas import (
    ComplaintAnalysisRequest,
    ComplaintAnalysisResponse,
)
from app.services.ai.detection_schemas import (
    RoadDamageAnalysisResult,
    RoadDamageDetectionRequest,
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
    - Runs local road damage computer vision (YOLO) if road image evidence is attached.
    - Computes deterministic explainable priority score (0-100).
    - Maps issue to responsible municipal department.
    Requires authenticated session.
    """
    analysis = await pipeline.analyze(request)
    return analysis


@router.post(
    "/detect-road-damage",
    response_model=RoadDamageAnalysisResult,
    summary="Detect Road Surface Damage via Local YOLO",
)
async def detect_road_damage(
    file: Optional[UploadFile] = File(None),
    media_url: Optional[str] = Form(None),
    confidence_threshold: Optional[float] = Form(0.35),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Executes local YOLO road damage detection on an uploaded image or an existing complaint media path:
    - Detects potholes (D40), alligator cracks (D20), longitudinal cracks (D00), and transverse cracks (D10).
    - Enforces input validation, file size bounds, and path traversal prevention.
    - Computes explainable visual damage score and original image pixel bounding boxes.
    Requires authenticated session.
    """
    detector = ModelRegistry.get_cv_detector()
    conf_thresh = confidence_threshold if confidence_threshold is not None else 0.35

    temp_created = False
    target_path = None

    try:
        if file is not None and file.filename:
            raw_filename = file.filename or "upload.bin"
            clean_basename = os.path.basename(raw_filename.replace("\\", "/"))
            if "." in clean_basename:
                ext = "." + clean_basename.rsplit(".", 1)[1].lower().strip()
            else:
                ext = ""

            if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported image format '{ext}'. Allowed formats: .jpg, .jpeg, .png, .webp",
                )

            max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
            contents = await file.read()
            if len(contents) == 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty image uploaded.")
            if len(contents) > max_bytes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Image exceeds maximum size limit of {settings.MAX_FILE_SIZE_MB}MB.",
                )

            os.makedirs(settings.MEDIA_UPLOAD_DIR, exist_ok=True)
            safe_name = f"cv_temp_{uuid.uuid4().hex[:12]}{ext}"
            target_path = os.path.join(settings.MEDIA_UPLOAD_DIR, safe_name)
            with open(target_path, "wb") as f:
                f.write(contents)
            temp_created = True

        elif media_url:
            clean_url = media_url.strip().replace("\\", "/")
            if not clean_url.startswith("/uploads/") or ".." in clean_url:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid media URL: only internal /uploads/ paths are accepted.",
                )
            safe_fname = os.path.basename(clean_url)
            target_path = os.path.join(settings.MEDIA_UPLOAD_DIR, safe_fname)
            if not os.path.isfile(target_path):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Specified media file does not exist on server.",
                )

            # Enforce complaint media ownership: if media is already attached to a complaint,
            # verify that citizen owns the complaint or is an official/admin
            media_record = db.query(ComplaintMedia).filter(ComplaintMedia.file_url == clean_url).first()
            if media_record and media_record.complaint:
                if current_user.role not in ["admin", "department_officer"]:
                    if media_record.complaint.citizen_id != current_user.id:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Access denied: You do not have permission to analyze media from this complaint.",
                        )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'file' upload or 'media_url' must be provided.",
            )

        result = detector.detect(target_path, confidence_threshold=conf_thresh)
        return result

    finally:
        if temp_created and target_path and os.path.isfile(target_path):
            try:
                os.remove(target_path)
            except Exception:
                pass


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
