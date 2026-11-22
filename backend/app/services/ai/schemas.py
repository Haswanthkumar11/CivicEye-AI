from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ComplaintAnalysisRequest(BaseModel):
    """Input payload for AI complaint analysis and triage."""
    text: str = Field(..., min_length=3, max_length=5000, description="Complaint headline, description, or transcript")
    category_hint: Optional[str] = Field(None, description="Optional citizen-selected category hint")
    location_hint: Optional[str] = Field(None, description="Optional address, landmark, or geographic notes")
    media_urls: Optional[List[str]] = Field(default=[], description="Optional list of associated /uploads/ media paths")


class GeminiExtractionResult(BaseModel):
    """Structured complaint data extracted via Gemini multimodal reasoning."""
    model_config = ConfigDict(from_attributes=True)

    complaint_category: str = Field(..., description="Controlled civic category (e.g. Road Infrastructure)")
    issue_type: str = Field(..., description="Specific problem subtype (e.g. Pothole / Road Cavity)")
    description_summary: str = Field(..., description="Concise objective synopsis of the civic defect")
    detected_damage: str = Field(..., description="Specific physical damage described or detected")
    estimated_damage_level: float = Field(..., ge=0.0, le=100.0, description="Estimated infrastructure damage (0-100)")
    potential_public_risk: float = Field(..., ge=0.0, le=100.0, description="Estimated safety hazard level (0-100)")
    affected_public_groups: str = Field(..., description="Key citizen groups impacted (e.g. Pedestrians, Commuters)")
    estimated_public_impact: float = Field(default=50.0, ge=0.0, le=100.0, description="Estimated public disruption, transit impact & citizen inconvenience factor (0-100)")
    location_sensitivity: float = Field(..., ge=0.0, le=100.0, description="Estimated location criticality factor (0-100)")
    recommended_department: str = Field(..., description="Controlled department code (e.g. ROADS, WATER, ELECTRICAL, PENDING_REVIEW)")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="AI extraction confidence (0.0 to 1.0)")
    reasoning: str = Field(..., description="Analytical justification explaining the category and risk assessment")


class SeverityFactorBreakdown(BaseModel):
    """Deterministic, explainable severity score computed mathematically by Python."""
    model_config = ConfigDict(from_attributes=True)

    damage_factor: float = Field(..., ge=0.0, le=100.0, description="Infrastructure physical damage (0.30 weight)")
    risk_factor: float = Field(..., ge=0.0, le=100.0, description="Public safety risk (0.30 weight)")
    public_impact_factor: float = Field(..., ge=0.0, le=100.0, description="Public impact & traffic disruption (0.20 weight)")
    location_sensitivity_factor: float = Field(..., ge=0.0, le=100.0, description="Location sensitivity & proximity (0.20 weight)")
    final_score: float = Field(..., ge=0.0, le=100.0, description="Final deterministic priority score (0-100)")
    severity_level: str = Field(..., description="LOW (0 to 30), MEDIUM (30 < S <= 60), HIGH (60 < S <= 80), CRITICAL (80 < S <= 100)")
    formula: str = Field(
        default="0.30 * Damage + 0.30 * Risk + 0.20 * Public Impact + 0.20 * Location Sensitivity",
        description="Exact deterministic formula applied",
    )
    calculation_explanation: str = Field(..., description="Human-readable breakdown explaining factor contributions")


class DepartmentRoutingResult(BaseModel):
    """Rules-based routing assignment with audit explanation."""
    model_config = ConfigDict(from_attributes=True)

    department_code: str = Field(..., description="Target department identifier: ROADS, WATER, SANITATION, DRAINAGE, ELECTRICAL, PUBLIC_INFRA, or PENDING_REVIEW")
    department_name: str = Field(..., description="Full municipal department name or Pending Administrative Triage")
    matched_rule: str = Field(..., description="Rule or keyword pattern that triggered the assignment")
    routing_explanation: str = Field(..., description="Administrative explanation for the routing decision")
    is_fallback: bool = Field(default=False, description="True if assigned via fallback triage protocol")
    requires_manual_review: bool = Field(default=False, description="True if complaint could not be routed with confidence and requires manual administrative review")


class ComplaintAnalysisResponse(BaseModel):
    """Combined output payload returned by the AI Intelligence Pipeline."""
    model_config = ConfigDict(from_attributes=True)

    status: str = Field(..., description="Processing status: COMPLETED, FALLBACK, or DISABLED")
    extraction: GeminiExtractionResult
    severity: SeverityFactorBreakdown
    routing: DepartmentRoutingResult
    yolo_analysis: Optional[Dict[str, Any]] = Field(default=None, description="Optional local road damage computer vision analysis")
    model_version: str = Field(default="gemini-3.8-flash", description="AI model / engine version tag")
    processing_time_ms: Optional[float] = Field(None, description="Pipeline latency in milliseconds")
