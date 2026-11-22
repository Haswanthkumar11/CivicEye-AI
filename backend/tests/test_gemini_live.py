import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.services.ai.gemini_service import GeminiService


def is_live_gemini_configured() -> bool:
    api_key = os.getenv("GEMINI_API_KEY", settings.GEMINI_API_KEY)
    if not api_key:
        return False
    cleaned = api_key.strip()
    return bool(cleaned and cleaned != "your-google-gemini-api-key-here")


@pytest.mark.skipif(
    not is_live_gemini_configured(),
    reason="Live Gemini API key not configured in environment (GEMINI_API_KEY). Skipping live network test.",
)
@pytest.mark.anyio
async def test_live_gemini_generation():
    """
    Separate live Gemini integration verification.
    Only executed when a real GEMINI_API_KEY is present in the environment.
    Strictly asserts structured extraction without exposing credentials.
    """
    service = GeminiService()
    assert service.is_available() is True

    test_prompt = "Large 3-foot deep pothole on NH-65 near Miyapur metro station causing major traffic congestion."
    result = await service.analyze_text(test_prompt, category_hint="Road Infrastructure")

    assert result is not None, "Live Gemini analysis returned None"
    assert result.complaint_category in [
        "Road Infrastructure", "Water Supply", "Sanitation",
        "Drainage", "Electricity and Streetlights", "Public Infrastructure", "Other"
    ]
    assert 0.0 <= result.estimated_damage_level <= 100.0
    assert 0.0 <= result.potential_public_risk <= 100.0
    assert 0.0 <= result.estimated_public_impact <= 100.0
    assert 0.0 <= result.location_sensitivity <= 100.0
    assert result.confidence_score > 0.0
