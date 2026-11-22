import os
import time
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.complaint import Complaint, AIAnalysisResult
from app.services.ai.schemas import (
    ComplaintAnalysisRequest,
    ComplaintAnalysisResponse,
)
from app.services.ai.gemini_service import GeminiService
from app.services.ai.complaint_extractor import ComplaintExtractor
from app.services.ai.severity_engine import SeverityEngine
from app.services.ai.department_router import DepartmentRouter
from app.services.ai.model_registry import ModelRegistry, IRoadDamageDetector

logger = logging.getLogger(__name__)


class AIPipeline:
    """
    Central orchestration pipeline for CivicEye AI grievance intelligence.
    Extracts structured complaints, scores priority deterministically,
    integrates local computer vision road damage evidence, and routes to departments.
    """

    def __init__(
        self,
        gemini_service: Optional[GeminiService] = None,
        extractor: Optional[ComplaintExtractor] = None,
        cv_detector: Optional[IRoadDamageDetector] = None,
    ):
        self.gemini = gemini_service or GeminiService()
        self.extractor = extractor or ComplaintExtractor(gemini_service=self.gemini)
        self.cv_detector = cv_detector

    async def analyze(self, request: ComplaintAnalysisRequest) -> ComplaintAnalysisResponse:
        """
        Executes end-to-end multimodal grievance analysis:
        1. Linguistic/multimodal extraction (Gemini or deterministic rule fallback).
        2. Local Road Damage computer vision (YOLO) on image evidence, if present.
        3. Deterministic priority & severity calculation via mathematical formula.
        4. Explainable rules-based municipal department routing.
        """
        start_time = time.perf_counter()

        enabled = getattr(settings, "AI_ANALYSIS_ENABLED", True)
        if not enabled:
            status = "DISABLED"
        else:
            status = "COMPLETED"

        # Step 1: Extraction
        extraction, is_fallback = await self.extractor.extract(
            text=request.text,
            category_hint=request.category_hint,
        )

        if is_fallback and status != "DISABLED":
            status = "FALLBACK"

        # Step 2: Visual Road Damage Analysis (Local YOLO)
        yolo_dict: Optional[Dict[str, Any]] = None
        visual_damage_score: Optional[float] = None
        visual_note: Optional[str] = None

        is_road_defect = (
            (request.category_hint and "road" in request.category_hint.lower())
            or (extraction.complaint_category and "road" in extraction.complaint_category.lower())
            or any(kw in request.text.lower() for kw in ["pothole", "crater", "crack", "asphalt", "road", "cavity"])
        )

        if is_road_defect and request.media_urls:
            for url in request.media_urls:
                clean_url = (url or "").replace("\\", "/")
                # Defensive check: ensure path is inside /uploads/ without traversal
                if clean_url.startswith("/uploads/") and ".." not in clean_url:
                    fname = os.path.basename(clean_url)
                    local_img_path = os.path.join(settings.MEDIA_UPLOAD_DIR, fname)
                    if os.path.isfile(local_img_path):
                        try:
                            detector = self.cv_detector or ModelRegistry.get_cv_detector()
                            cv_result = detector.detect(local_img_path)
                            yolo_dict = cv_result.model_dump()
                            if cv_result.processing_status == "SUCCESS" and cv_result.detection_count > 0:
                                visual_damage_score = cv_result.estimated_visual_damage_level
                                visual_note = cv_result.visual_evidence_explanation
                            break
                        except Exception as e:
                            logger.warning(f"Local YOLO analysis error on '{local_img_path}': {e}")

        # Step 3: Deterministic Severity Calculation (Python mathematical formula)
        # S = 0.30*Damage + 0.30*Risk + 0.20*Impact + 0.20*Sensitivity
        if visual_damage_score is not None:
            # Fuse linguistic damage with visual computer vision evidence: 60% text, 40% visual
            combined_damage = round(0.60 * extraction.estimated_damage_level + 0.40 * visual_damage_score, 2)
        else:
            combined_damage = extraction.estimated_damage_level

        severity = SeverityEngine.calculate(
            damage_factor=combined_damage,
            risk_factor=extraction.potential_public_risk,
            public_impact_factor=extraction.estimated_public_impact,
            location_sensitivity_factor=extraction.location_sensitivity,
        )

        if visual_note:
            severity.calculation_explanation += f" [{visual_note}]"

        # Step 4: Rules-Based Department Routing
        routing = DepartmentRouter.route(
            category=extraction.complaint_category,
            issue_type=extraction.issue_type,
            text=request.text,
        )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        model_version = settings.GEMINI_MODEL if status == "COMPLETED" else "deterministic-rule-engine-v1"

        return ComplaintAnalysisResponse(
            status=status,
            extraction=extraction,
            severity=severity,
            routing=routing,
            yolo_analysis=yolo_dict,
            model_version=model_version,
            processing_time_ms=elapsed_ms,
        )

    def persist_result(
        self,
        db: Session,
        complaint_id: str,
        analysis: ComplaintAnalysisResponse,
    ) -> AIAnalysisResult:
        """
        Persists structured AI analysis output to the relational database (ai_analysis_results table).
        Implements idempotent upsert: if an analysis record already exists for this complaint,
        it updates the record in place to prevent uncontrolled duplicates.
        Also synchronizes computed severity and risk onto the parent complaint record.
        """
        metadata_payload = {
            "pipeline_status": analysis.status,
            "model_version": analysis.model_version,
            "latency_ms": analysis.processing_time_ms,
            "routing": analysis.routing.model_dump(),
            "severity_level": analysis.severity.severity_level,
            "calculation_explanation": analysis.severity.calculation_explanation,
            "formula": analysis.severity.formula,
        }

        existing = db.query(AIAnalysisResult).filter(AIAnalysisResult.complaint_id == complaint_id).first()
        if existing:
            existing.language_detected = "en"
            existing.yolo_detections = analysis.yolo_analysis
            existing.gemini_analysis = analysis.extraction.model_dump()
            existing.damage_score = analysis.severity.damage_factor
            existing.risk_score = analysis.severity.risk_factor
            existing.impact_score = analysis.severity.public_impact_factor
            existing.sensitivity_score = analysis.severity.location_sensitivity_factor
            existing.calculated_severity = analysis.severity.final_score
            existing.model_versions = metadata_payload
            record = existing
        else:
            record = AIAnalysisResult(
                complaint_id=complaint_id,
                language_detected="en",
                transcription_text=None,
                yolo_detections=analysis.yolo_analysis,
                gemini_analysis=analysis.extraction.model_dump(),
                damage_score=analysis.severity.damage_factor,
                risk_score=analysis.severity.risk_factor,
                impact_score=analysis.severity.public_impact_factor,
                sensitivity_score=analysis.severity.location_sensitivity_factor,
                calculated_severity=analysis.severity.final_score,
                model_versions=metadata_payload,
            )
            db.add(record)

        # Synchronize computed priority score back onto the parent complaint record
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if complaint:
            complaint.severity = analysis.severity.severity_level
            complaint.severity_score = analysis.severity.final_score
            complaint.risk_level = analysis.severity.severity_level

        db.commit()
        db.refresh(record)
        return record

        # Synchronize computed priority score back onto the parent complaint record
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if complaint:
            complaint.severity = analysis.severity.severity_level
            complaint.severity_score = analysis.severity.final_score
            complaint.risk_level = analysis.severity.severity_level

        db.commit()
        db.refresh(record)
        return record
