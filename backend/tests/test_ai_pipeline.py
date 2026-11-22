import sys
import os
import io
import json
import uuid
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.db.init_db import init_db
from app.core.database import SessionLocal
from app.models.complaint import Complaint, AIAnalysisResult
from app.services.ai.schemas import (
    ComplaintAnalysisRequest,
    ComplaintAnalysisResponse,
    GeminiExtractionResult,
    SeverityFactorBreakdown,
    DepartmentRoutingResult,
)
from app.services.ai.severity_engine import SeverityEngine, clamp_factor, get_severity_level
from app.services.ai.department_router import DepartmentRouter
from app.services.ai.gemini_service import GeminiService
from app.services.ai.complaint_extractor import ComplaintExtractor
from app.services.ai.ai_pipeline import AIPipeline
from app.services.ai.model_registry import ModelRegistry

init_db()
client = TestClient(app)


def get_citizen_token():
    res = client.post("/api/auth/demo-login", json={"role": "citizen"})
    assert res.status_code == 200
    return res.json()["access_token"]


# ==============================================================================
# 1. Severity Calculation & Formula Tests
# ==============================================================================

def test_severity_calculation_exact():
    """
    Formula: S = 0.30*Damage + 0.30*Risk + 0.20*Impact + 0.20*Sensitivity
    Inputs: Damage=80, Risk=90, Impact=50, Sensitivity=70
    Expected: 0.30*80 + 0.30*90 + 0.20*50 + 0.20*70 = 24 + 27 + 10 + 14 = 75.0
    Tier: HIGH
    """
    res = SeverityEngine.calculate(
        damage_factor=80.0,
        risk_factor=90.0,
        public_impact_factor=50.0,
        location_sensitivity_factor=70.0,
    )
    assert res.final_score == 75.0
    assert res.severity_level == "HIGH"
    assert res.damage_factor == 80.0
    assert res.risk_factor == 90.0
    assert res.public_impact_factor == 50.0
    assert res.location_sensitivity_factor == 70.0
    assert "75.0/100 (HIGH)" in res.calculation_explanation


def test_severity_calculation_zero_and_max():
    # Min boundary
    res_min = SeverityEngine.calculate(0.0, 0.0, 0.0, 0.0)
    assert res_min.final_score == 0.0
    assert res_min.severity_level == "LOW"

    # Max boundary
    res_max = SeverityEngine.calculate(100.0, 100.0, 100.0, 100.0)
    assert res_max.final_score == 100.0
    assert res_max.severity_level == "CRITICAL"


def test_all_four_severity_factors_individually_contribute():
    """
    Validates that each of the 4 factors contributes according to its exact weight:
      - Damage: 0.30
      - Risk: 0.30
      - Public Impact: 0.20
      - Location Sensitivity: 0.20
    """
    # Damage only
    res_d = SeverityEngine.calculate(damage_factor=100.0, risk_factor=0.0, public_impact_factor=0.0, location_sensitivity_factor=0.0)
    assert res_d.final_score == 30.0

    # Risk only
    res_r = SeverityEngine.calculate(damage_factor=0.0, risk_factor=100.0, public_impact_factor=0.0, location_sensitivity_factor=0.0)
    assert res_r.final_score == 30.0

    # Public Impact only
    res_i = SeverityEngine.calculate(damage_factor=0.0, risk_factor=0.0, public_impact_factor=100.0, location_sensitivity_factor=0.0)
    assert res_i.final_score == 20.0

    # Location Sensitivity only
    res_s = SeverityEngine.calculate(damage_factor=0.0, risk_factor=0.0, public_impact_factor=0.0, location_sensitivity_factor=100.0)
    assert res_s.final_score == 20.0

    # Additive sum of all 4 factors
    res_all = SeverityEngine.calculate(damage_factor=100.0, risk_factor=100.0, public_impact_factor=100.0, location_sensitivity_factor=100.0)
    assert res_all.final_score == 100.0


# ==============================================================================
# 2. Continuous Severity Boundary Tests
# ==============================================================================

def test_severity_continuous_boundaries():
    """
    Standardized Continuous Priority Tiers:
      - LOW: 0.0 <= S <= 30.0
      - MEDIUM: 30.0 < S <= 60.0
      - HIGH: 60.0 < S <= 80.0
      - CRITICAL: 80.0 < S <= 100.0
    Asserts exact boundary points: 30, 30.01, 60, 60.01, 80, 80.01, and 100.
    """
    assert get_severity_level(0.0) == "LOW"
    assert get_severity_level(30.0) == "LOW"
    assert get_severity_level(30.01) == "MEDIUM"
    assert get_severity_level(60.0) == "MEDIUM"
    assert get_severity_level(60.01) == "HIGH"
    assert get_severity_level(80.0) == "HIGH"
    assert get_severity_level(80.01) == "CRITICAL"
    assert get_severity_level(100.0) == "CRITICAL"


# ==============================================================================
# 3. Invalid & Out-of-Range Severity Inputs
# ==============================================================================

def test_invalid_severity_inputs_clamped():
    # Values above 100 should be clamped to 100
    res_high = SeverityEngine.calculate(
        damage_factor=150.0,
        risk_factor=200.0,
        public_impact_factor=999.0,
        location_sensitivity_factor=105.0,
    )
    assert res_high.damage_factor == 100.0
    assert res_high.risk_factor == 100.0
    assert res_high.public_impact_factor == 100.0
    assert res_high.location_sensitivity_factor == 100.0
    assert res_high.final_score == 100.0
    assert res_high.severity_level == "CRITICAL"

    # Negative values should be clamped to 0
    res_low = SeverityEngine.calculate(
        damage_factor=-50.0,
        risk_factor=-10.0,
        public_impact_factor=-0.5,
        location_sensitivity_factor=-100.0,
    )
    assert res_low.damage_factor == 0.0
    assert res_low.risk_factor == 0.0
    assert res_low.public_impact_factor == 0.0
    assert res_low.location_sensitivity_factor == 0.0
    assert res_low.final_score == 0.0
    assert res_low.severity_level == "LOW"

    # None and NaN fallback to default 50.0
    res_none = SeverityEngine.calculate(None, None, None, None)
    assert res_none.damage_factor == 50.0
    assert res_none.public_impact_factor == 50.0
    assert res_none.final_score == 50.0
    assert res_none.severity_level == "MEDIUM"


# ==============================================================================
# 4. Department Routing for Each Supported Category
# ==============================================================================

@pytest.mark.parametrize(
    "category,text,expected_code,expected_name",
    [
        ("Road Infrastructure", "deep crater pothole in the asphalt", "ROADS", "Municipal Roads & Infrastructure"),
        ("Water Supply", "drinking water pipeline burst and leaking", "WATER", "Water Supply & Sewerage Board"),
        ("Sanitation", "illegal garbage accumulation overflowing dustbin", "SANITATION", "Solid Waste Management & Sanitation"),
        ("Drainage", "clogged storm drain causing sewage overflow", "DRAINAGE", "Storm Water & Surface Drainage"),
        ("Electricity and Streetlights", "dark streetlight sparking electric pole", "ELECTRICAL", "Electricity & Public Lighting"),
        ("Public Infrastructure", "broken footpath and damaged bus shelter", "PUBLIC_INFRA", "Public Infrastructure & Parks"),
    ],
)
def test_department_routing_supported_categories(category, text, expected_code, expected_name):
    routing = DepartmentRouter.route(category=category, text=text)
    assert routing.department_code == expected_code
    assert routing.department_name == expected_name
    assert routing.is_fallback is False
    assert routing.requires_manual_review is False


def test_department_routing_by_keywords_without_category():
    # Only text provided, no category
    routing_roads = DepartmentRouter.route(text="Dangerous road potholes and asphalt cracks on main street")
    assert routing_roads.department_code == "ROADS"
    assert routing_roads.is_fallback is False
    assert routing_roads.requires_manual_review is False

    routing_water = DepartmentRouter.route(text="Contaminated tap water pouring muddy water from pipeline leak")
    assert routing_water.department_code == "WATER"

    routing_elec = DepartmentRouter.route(text="Sparking transformer and dangling live wires near school")
    assert routing_elec.department_code == "ELECTRICAL"


# ==============================================================================
# 5. Unknown Complaint Fallback & Manual Review Flagging
# ==============================================================================

def test_unknown_complaint_routing_requires_manual_review():
    """
    Unmatched complaints MUST NOT be silently routed to ROADS.
    They must be flagged with requires_manual_review = True and is_fallback = True.
    """
    routing = DepartmentRouter.route(text="Unspecified matter with zero keywords xxyyzz")
    assert routing.is_fallback is True
    assert routing.requires_manual_review is True
    assert routing.department_code == "PENDING_REVIEW"
    assert routing.department_name == "Pending Administrative Triage"
    assert "manual administrative review" in routing.routing_explanation.lower()


# ==============================================================================
# 6. Fallback Public Impact & Sensitivity Estimation
# ==============================================================================

def test_public_impact_factor_rule_estimation():
    extractor = ComplaintExtractor()

    # 1. High impact transit corridor
    res_transit = extractor._fallback_extraction("Dangerous pothole near metro station bus stop with heavy traffic commuters")
    assert res_transit.estimated_public_impact == 80.0
    assert "commuters" in res_transit.affected_public_groups.lower()

    # 2. Sensitive facility (school/hospital)
    res_school = extractor._fallback_extraction("Open sparking live wire near public school and children playground")
    assert res_school.location_sensitivity == 85.0
    assert res_school.estimated_public_impact >= 65.0
    assert "schoolchildren" in res_school.affected_public_groups.lower()

    # 3. Isolated / remote cul-de-sac
    res_remote = extractor._fallback_extraction("Pothole in isolated deserted alley dead end")
    assert res_remote.estimated_public_impact == 35.0
    assert res_remote.location_sensitivity == 30.0

    # 4. Neutral text without crowd indicators (conservative baseline)
    res_neutral = extractor._fallback_extraction("Pothole on asphalt street")
    assert res_neutral.estimated_public_impact == 50.0


# ==============================================================================
# 7. Pydantic Response Validation
# ==============================================================================

def test_pydantic_schema_validation():
    # Valid extraction
    valid_data = {
        "complaint_category": "Road Infrastructure",
        "issue_type": "Pothole",
        "description_summary": "Deep cavity on road",
        "detected_damage": "Asphalt crater",
        "estimated_damage_level": 75.0,
        "potential_public_risk": 80.0,
        "affected_public_groups": "Motorists",
        "estimated_public_impact": 70.0,
        "location_sensitivity": 60.0,
        "recommended_department": "ROADS",
        "confidence_score": 0.95,
        "reasoning": "Road safety risk",
    }
    obj = GeminiExtractionResult(**valid_data)
    assert obj.estimated_damage_level == 75.0
    assert obj.estimated_public_impact == 70.0
    assert obj.confidence_score == 0.95

    # Out of range confidence score should raise ValidationError
    invalid_data = valid_data.copy()
    invalid_data["confidence_score"] = 1.5
    with pytest.raises(Exception):
        GeminiExtractionResult(**invalid_data)


# ==============================================================================
# 8. Gemini Service Mocked Success & Failure Handling
# ==============================================================================

@pytest.mark.anyio
async def test_gemini_service_mocked_success():
    mock_dict = {
        "complaint_category": "Water Supply",
        "issue_type": "Pipe Burst",
        "description_summary": "High pressure pipe burst flooding neighborhood street",
        "detected_damage": "Broken main water valve",
        "estimated_damage_level": 85.0,
        "potential_public_risk": 70.0,
        "affected_public_groups": "Local households and traffic",
        "estimated_public_impact": 75.0,
        "location_sensitivity": 65.0,
        "recommended_department": "WATER",
        "confidence_score": 0.92,
        "reasoning": "Urgent water loss and potential contamination hazard",
    }
    raw_json_str = json.dumps(mock_dict)

    service = GeminiService()
    service.api_key = "dummy_test_key_for_mocking"

    mock_resp = MagicMock()
    mock_resp.text = raw_json_str

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_resp)

    with patch.object(service, "_get_client", return_value=mock_client), \
         patch.object(service, "is_available", return_value=True):
        result = await service.analyze_text("Massive water pipe burst near market")
        assert result is not None
        assert result.complaint_category == "Water Supply"
        assert result.recommended_department == "WATER"
        assert result.estimated_damage_level == 85.0
        assert result.estimated_public_impact == 75.0


@pytest.mark.anyio
async def test_gemini_failure_and_fallback():
    service = GeminiService()
    # Simulate API failure / network exception
    with patch.object(service, "is_available", return_value=True), \
         patch.object(service, "analyze_text", return_value=None):
        extractor = ComplaintExtractor(gemini_service=service)
        result, is_fallback = await extractor.extract("Hazardous pothole causing accidents on highway")
        assert is_fallback is True
        assert result.complaint_category == "Road Infrastructure"
        assert result.recommended_department == "ROADS"
        assert result.estimated_public_impact > 0.0
        assert "Gemini fallback" in result.reasoning


# ==============================================================================
# 9. Missing Gemini API Key Handling
# ==============================================================================

@pytest.mark.anyio
async def test_missing_gemini_api_key_deterministic_fallback():
    pipeline = AIPipeline()
    # Force API key to empty string
    pipeline.gemini.api_key = ""
    assert pipeline.gemini.is_available() is False

    req = ComplaintAnalysisRequest(
        text="Dark streetlight and exposed sparking live wire near school junction",
    )
    res = await pipeline.analyze(req)
    assert res.status == "FALLBACK"
    assert res.routing.department_code == "ELECTRICAL"
    assert res.severity.final_score > 0
    assert res.severity.public_impact_factor > 0
    assert res.severity.severity_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


# ==============================================================================
# 10. API Endpoint Authentication & Integration Tests
# ==============================================================================

def test_analyze_complaint_unauthenticated_rejected():
    res = client.post("/api/ai/analyze-complaint", json={"text": "Road cavity causing accidents"})
    assert res.status_code == 401


def test_analyze_complaint_authenticated_success():
    token = get_citizen_token()
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "text": "Huge hazardous pothole on arterial road damaging vehicles",
        "category_hint": "Road Infrastructure",
    }
    res = client.post("/api/ai/analyze-complaint", json=payload, headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert "status" in data
    assert "extraction" in data
    assert "severity" in data
    assert "routing" in data
    assert data["routing"]["department_code"] == "ROADS"
    assert data["severity"]["final_score"] >= 0.0
    assert "public_impact_factor" in data["severity"]


def test_ai_status_endpoint():
    token = get_citizen_token()
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/ai/status", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "target_hardware" in data
    assert "NVIDIA GeForce GTX 1650" in data["target_hardware"]["gpu"]
    assert "gemini_model" in data


# ==============================================================================
# 11. Database Persistence & Upsert Idempotency
# ==============================================================================

@pytest.mark.anyio
async def test_ai_result_database_persistence():
    token = get_citizen_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a complaint
    c_res = client.post("/api/complaints", json={
        "title": "Severe Water Main Break",
        "description": "High pressure potable water main burst flooding basements.",
        "category": "Water Supply",
    }, headers=headers)
    assert c_res.status_code == 201
    complaint_id = c_res.json()["id"]

    # 2. Run AI pipeline and persist to database
    pipeline = AIPipeline()
    req = ComplaintAnalysisRequest(
        text="High pressure potable water main burst flooding basements.",
        category_hint="Water Supply",
    )
    analysis = await pipeline.analyze(req)

    db = SessionLocal()
    try:
        record = pipeline.persist_result(db, complaint_id, analysis)
        assert record.id is not None
        assert record.complaint_id == complaint_id
        assert record.calculated_severity == analysis.severity.final_score
        assert record.impact_score == analysis.severity.public_impact_factor
        assert record.gemini_analysis["recommended_department"] == "WATER"
    finally:
        db.close()


@pytest.mark.anyio
async def test_repeated_analysis_idempotent_upsert():
    """
    Ensures repeated analysis of the same complaint updates the existing AIAnalysisResult
    in-place without creating uncontrolled duplicate rows.
    """
    token = get_citizen_token()
    headers = {"Authorization": f"Bearer {token}"}

    c_res = client.post("/api/complaints", json={
        "title": "Clogged Storm Drain",
        "description": "Monsoon stormwater drain completely blocked with plastic debris.",
        "category": "Drainage",
    }, headers=headers)
    assert c_res.status_code == 201
    complaint_id = c_res.json()["id"]

    pipeline = AIPipeline()
    req = ComplaintAnalysisRequest(
        text="Monsoon stormwater drain completely blocked with plastic debris.",
        category_hint="Drainage",
    )

    db = SessionLocal()
    try:
        # Initial analysis
        analysis1 = await pipeline.analyze(req)
        record1 = pipeline.persist_result(db, complaint_id, analysis1)
        record1_id = record1.id

        total_count_1 = db.query(AIAnalysisResult).filter(AIAnalysisResult.complaint_id == complaint_id).count()
        assert total_count_1 == 1

        # Second analysis (e.g. updated report or re-triage)
        analysis2 = await pipeline.analyze(req)
        # Manually alter a factor to verify update took effect
        analysis2.severity.final_score = 88.5
        record2 = pipeline.persist_result(db, complaint_id, analysis2)

        total_count_2 = db.query(AIAnalysisResult).filter(AIAnalysisResult.complaint_id == complaint_id).count()
        assert total_count_2 == 1, "Duplicate AIAnalysisResult row was created instead of updating in-place!"
        assert record2.id == record1_id
        assert record2.calculated_severity == 88.5

        # Verify parent complaint record was synchronized
        parent_complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        assert parent_complaint.severity_score == 88.5
    finally:
        db.close()
