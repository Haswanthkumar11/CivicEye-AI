import time
import logging
from typing import Optional, Dict, Any
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

logger = logging.getLogger(__name__)


class AIPipeline:
    """
    Central orchestration pipeline for CivicEye AI grievance intelligence.
    Extracts structured complaints, scores priority deterministically, and routes to departments.
    """

    def __init__(
        self,
        gemini_service: Optional[GeminiService] = None,
        extractor: Optional[ComplaintExtractor] = None,
    ):
        self.gemini = gemini_service or GeminiService()
        self.extractor = extractor or ComplaintExtractor(gemini_service=self.gemini)

    async def analyze(self, request: ComplaintAnalysisRequest) -> ComplaintAnalysisResponse:
        """
        Executes end-to-end multimodal grievance analysis:
        1. Linguistic/multimodal extraction (Gemini or deterministic rule fallback).
        2. Deterministic priority & severity calculation via mathematical formula.
        3. Explainable rules-based municipal department routing.
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

        # Step 2: Deterministic Severity Calculation (Python mathematical formula)
        # S = 0.30*Damage + 0.30*Risk + 0.20*Impact + 0.20*Sensitivity
        severity = SeverityEngine.calculate(
            damage_factor=extraction.estimated_damage_level,
            risk_factor=extraction.potential_public_risk,
            public_impact_factor=50.0,  # Baseline public impact from text hints
            location_sensitivity_factor=extraction.location_sensitivity,
        )

        # Step 3: Rules-Based Department Routing
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
        """
        record = AIAnalysisResult(
            complaint_id=complaint_id,
            language_detected="en",
            transcription_text=None,
            yolo_detections=None,
            gemini_analysis=analysis.extraction.model_dump(),
            damage_score=analysis.severity.damage_factor,
            risk_score=analysis.severity.risk_factor,
            impact_score=analysis.severity.public_impact_factor,
            sensitivity_score=analysis.severity.location_sensitivity_factor,
            calculated_severity=analysis.severity.final_score,
            model_versions={
                "pipeline_status": analysis.status,
                "model_version": analysis.model_version,
                "latency_ms": analysis.processing_time_ms,
            },
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
