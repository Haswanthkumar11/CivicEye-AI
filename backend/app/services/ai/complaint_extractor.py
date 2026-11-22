import re
from typing import Optional, Dict, Any, Tuple
from app.services.ai.schemas import GeminiExtractionResult
from app.services.ai.gemini_service import GeminiService
from app.services.ai.department_router import DepartmentRouter, CATEGORY_TO_DEPT_CODE


# High-severity signal keywords for fallback estimation
HIGH_RISK_KEYWORDS = [
    "danger", "dangerous", "accident", "accidents", "hazard", "fatal", "injury", "injured",
    "collapse", "cave-in", "spark", "sparking", "live wire", "burst", "flood", "flooding",
    "emergency", "urgent", "severe", "critical", "deep", "crater"
]

MEDIUM_RISK_KEYWORDS = [
    "broken", "damage", "damaged", "leak", "leaking", "overflow", "clogged", "dark",
    "crack", "pothole", "garbage", "trash", "smell", "stagnant", "delay", "nuisance"
]


class ComplaintExtractor:
    """
    Coordinates complaint intelligence extraction.
    Leverages Gemini multimodal model with deterministic rule-based fallback.
    """

    def __init__(self, gemini_service: Optional[GeminiService] = None):
        self.gemini = gemini_service or GeminiService()

    async def extract(self, text: str, category_hint: Optional[str] = None) -> Tuple[GeminiExtractionResult, bool]:
        """
        Extracts structured complaint intelligence.
        Returns: (GeminiExtractionResult, is_fallback: bool)
        """
        # Try Gemini extraction if available
        if self.gemini.is_available():
            gemini_result = await self.gemini.analyze_text(text, category_hint=category_hint)
            if gemini_result is not None:
                return gemini_result, False

        # Graceful fallback to deterministic rule engine
        fallback_result = self._fallback_extraction(text, category_hint=category_hint)
        return fallback_result, True

    def _fallback_extraction(self, text: str, category_hint: Optional[str] = None) -> GeminiExtractionResult:
        """
        Deterministic rule-based extraction used when Gemini is unavailable, rate-limited, or offline.
        Analyzes grievance text using keyword heuristics and category rules.
        """
        routing = DepartmentRouter.route(category=category_hint, text=text)
        dept_code = routing.department_code

        # Map dept_code back to standardized category
        dept_to_category = {
            "ROADS": "Road Infrastructure",
            "WATER": "Water Supply",
            "SANITATION": "Sanitation",
            "DRAINAGE": "Drainage",
            "ELECTRICAL": "Electricity and Streetlights",
            "PUBLIC_INFRA": "Public Infrastructure",
        }
        category = category_hint or dept_to_category.get(dept_code, "Road Infrastructure")

        lower_text = text.lower()

        # Determine issue type from keywords
        if "pothole" in lower_text or "crater" in lower_text:
            issue_type = "Pothole / Road Cavity"
        elif "pipe" in lower_text or "burst" in lower_text:
            issue_type = "Pipe Leak / Burst"
        elif "garbage" in lower_text or "waste" in lower_text or "trash" in lower_text:
            issue_type = "Garbage Pileup"
        elif "drain" in lower_text or "sewage" in lower_text or "sewer" in lower_text:
            issue_type = "Clogged Storm Drain"
        elif "light" in lower_text or "wire" in lower_text or "pole" in lower_text:
            issue_type = "Dark Streetlight / Wire Hazard"
        elif "footpath" in lower_text or "shelter" in lower_text:
            issue_type = "Damaged Public Infrastructure"
        else:
            issue_type = f"{category} Issue"

        # Estimate damage and risk factors from signal keywords
        high_matches = sum(1 for kw in HIGH_RISK_KEYWORDS if re.search(r"\b" + re.escape(kw) + r"\b", lower_text))
        med_matches = sum(1 for kw in MEDIUM_RISK_KEYWORDS if re.search(r"\b" + re.escape(kw) + r"\b", lower_text))

        if high_matches >= 2:
            damage_score = 80.0
            risk_score = 85.0
            sensitivity_score = 75.0
        elif high_matches == 1 or med_matches >= 2:
            damage_score = 65.0
            risk_score = 65.0
            sensitivity_score = 60.0
        elif med_matches == 1:
            damage_score = 50.0
            risk_score = 45.0
            sensitivity_score = 50.0
        else:
            damage_score = 40.0
            risk_score = 35.0
            sensitivity_score = 40.0

        summary = text.strip()[:140] + ("..." if len(text) > 140 else "")

        return GeminiExtractionResult(
            complaint_category=category,
            issue_type=issue_type,
            description_summary=summary,
            detected_damage=f"Physical civic defect identified via rule-based keyword triage ({issue_type})",
            estimated_damage_level=damage_score,
            potential_public_risk=risk_score,
            affected_public_groups="Commuters, pedestrians, and nearby residents",
            location_sensitivity=sensitivity_score,
            recommended_department=dept_code,
            confidence_score=0.75,
            reasoning="Extracted via deterministic linguistic rule base (Gemini fallback mode).",
        )
