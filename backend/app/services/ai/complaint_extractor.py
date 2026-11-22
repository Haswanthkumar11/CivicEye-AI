import re
from typing import Optional, Dict, Any, Tuple
from app.services.ai.schemas import GeminiExtractionResult
from app.services.ai.gemini_service import GeminiService
from app.services.ai.department_router import DepartmentRouter, CATEGORY_TO_DEPT_CODE


# Signal keywords for fallback estimation
HIGH_RISK_KEYWORDS = [
    "danger", "dangerous", "accident", "accidents", "hazard", "fatal", "injury", "injured",
    "collapse", "cave-in", "spark", "sparking", "live wire", "burst", "flood", "flooding",
    "emergency", "urgent", "severe", "critical", "deep", "crater"
]

MEDIUM_RISK_KEYWORDS = [
    "broken", "damage", "damaged", "leak", "leaking", "overflow", "clogged", "dark",
    "crack", "pothole", "garbage", "trash", "smell", "stagnant", "delay", "nuisance"
]

PUBLIC_IMPACT_HIGH_KEYWORDS = [
    "transit", "metro", "bus", "buses", "station", "highway", "arterial", "main road",
    "junction", "intersection", "flyover", "market", "commuters", "traffic jam", "rush hour",
    "crowd", "dense traffic", "two-wheeler", "pedestrian", "pedestrians"
]

SENSITIVE_FACILITIES_KEYWORDS = [
    "school", "hospital", "clinic", "kindergarten", "college", "dispensary", "nursing home",
    "temple", "church", "mosque", "daycare", "playground"
]

PUBLIC_IMPACT_LOW_KEYWORDS = [
    "isolated", "remote", "dead end", "cul-de-sac", "alley", "vacant", "deserted", "service lane"
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
        Analyzes grievance text using keyword heuristics, sensitive facility recognition, and category rules.
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
        if dept_code in dept_to_category:
            category = category_hint or dept_to_category[dept_code]
        else:
            category = category_hint or "Other"

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
            issue_type = f"{category} Issue" if category != "Other" else "Unclassified Civic Defect"

        # 1. Damage and Risk Factors from Hazard Keywords
        high_matches = sum(1 for kw in HIGH_RISK_KEYWORDS if re.search(r"\b" + re.escape(kw) + r"\b", lower_text))
        med_matches = sum(1 for kw in MEDIUM_RISK_KEYWORDS if re.search(r"\b" + re.escape(kw) + r"\b", lower_text))

        if high_matches >= 2:
            damage_score = 80.0
            risk_score = 85.0
        elif high_matches == 1 or med_matches >= 2:
            damage_score = 65.0
            risk_score = 65.0
        elif med_matches == 1:
            damage_score = 50.0
            risk_score = 45.0
        else:
            damage_score = 40.0
            risk_score = 35.0

        # 2. Dedicated Public Impact Factor Estimation
        impact_high_matches = sum(1 for kw in PUBLIC_IMPACT_HIGH_KEYWORDS if re.search(r"\b" + re.escape(kw) + r"\b", lower_text))
        facility_matches = sum(1 for kw in SENSITIVE_FACILITIES_KEYWORDS if re.search(r"\b" + re.escape(kw) + r"\b", lower_text))
        impact_low_matches = sum(1 for kw in PUBLIC_IMPACT_LOW_KEYWORDS if re.search(r"\b" + re.escape(kw) + r"\b", lower_text))

        if impact_high_matches >= 2 or (impact_high_matches >= 1 and facility_matches >= 1):
            public_impact = 80.0
        elif impact_high_matches == 1 or facility_matches >= 1:
            public_impact = 65.0
        elif impact_low_matches >= 1:
            public_impact = 35.0
        else:
            # Conservative baseline when grievance text provides no explicit transit or footfall indicators
            public_impact = 50.0

        # 3. Location Sensitivity Factor Estimation
        if facility_matches >= 1:
            # High proximity sensitivity (schools, hospitals, clinics)
            sensitivity_score = 85.0
        elif impact_high_matches >= 1:
            # Arterial junctions, highway corridors, central commercial zones
            sensitivity_score = 70.0
        elif impact_low_matches >= 1:
            # Remote or isolated cul-de-sac
            sensitivity_score = 30.0
        else:
            # Standard residential baseline
            sensitivity_score = 50.0

        # 4. Impacted Citizen Groups Breakdown
        affected_groups = []
        if facility_matches >= 1:
            affected_groups.append("Schoolchildren, patients & visitors")
        if impact_high_matches >= 1:
            affected_groups.append("Daily commuters & vehicular traffic")
        if not affected_groups:
            affected_groups.append("Local residents and neighborhood pedestrians")
        affected_str = "; ".join(affected_groups)

        summary = text.strip()[:140] + ("..." if len(text) > 140 else "")

        return GeminiExtractionResult(
            complaint_category=category,
            issue_type=issue_type,
            description_summary=summary,
            detected_damage=f"Physical civic defect identified via rule-based keyword triage ({issue_type})",
            estimated_damage_level=damage_score,
            potential_public_risk=risk_score,
            affected_public_groups=affected_str,
            estimated_public_impact=public_impact,
            location_sensitivity=sensitivity_score,
            recommended_department=dept_code,
            confidence_score=0.75,
            reasoning="Extracted via deterministic linguistic rule base (Gemini fallback mode).",
        )
