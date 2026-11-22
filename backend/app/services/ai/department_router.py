import re
from typing import Dict, Any, Optional, Tuple
from app.services.ai.schemas import DepartmentRoutingResult


# Master Department Directory matching database seeds in backend/app/db/init_db.py
DEPARTMENTS = {
    "ROADS": {
        "name": "Municipal Roads & Infrastructure",
        "description": "Potholes, asphalt wear, road cave-ins, dividers, guardrails, and street surfaces.",
        "keywords": [
            "pothole", "potholes", "road", "roads", "asphalt", "tar", "divider", "guardrail",
            "cave-in", "crater", "pavement", "crack", "cracks", "speedbreaker", "curb", "kerb",
            "traffic barrier", "damaged road", "sunken road",
        ],
    },
    "WATER": {
        "name": "Water Supply & Sewerage Board",
        "description": "Drinking water supply, main leaks, pipe bursts, low pressure, and water contamination.",
        "keywords": [
            "water", "pipe", "pipes", "pipeline", "leak", "leaking", "leakage", "burst",
            "drinking water", "tap", "taps", "contaminated water", "dirty water", "muddy water",
            "low pressure", "no water", "water supply", "valve", "broken pipe",
        ],
    },
    "SANITATION": {
        "name": "Solid Waste Management & Sanitation",
        "description": "Garbage accumulation, illegal dumping, overflowing dustbins, and animal carcasses.",
        "keywords": [
            "garbage", "waste", "trash", "dump", "dumping", "dustbin", "litter", "debris",
            "carcass", "dead animal", "stench", "rubbish", "sweeper", "refuse", "waste burning",
            "plastic waste", "overflowing bin", "filth",
        ],
    },
    "DRAINAGE": {
        "name": "Storm Water & Surface Drainage",
        "description": "Clogged storm drains, sewage overflows, open manholes, and monsoon waterlogging.",
        "keywords": [
            "drain", "drainage", "storm drain", "sewer", "sewerage", "manhole", "open sewer",
            "overflow", "overflowing sewage", "clogged", "choked", "blockage", "waterlogging",
            "flooding", "gutters", "stormwater", "stagnant water",
        ],
    },
    "ELECTRICAL": {
        "name": "Electricity & Public Lighting",
        "description": "Streetlight outages, exposed live wires, sparking poles, and damaged transformers.",
        "keywords": [
            "light", "lights", "streetlight", "streetlights", "lamp", "lighting", "electricity",
            "electric", "wire", "wires", "live wire", "hanging wire", "pole", "electric pole",
            "transformer", "spark", "sparking", "blackout", "dark junction", "power outage",
        ],
    },
    "PUBLIC_INFRA": {
        "name": "Public Infrastructure & Parks",
        "description": "Damaged footpaths, broken bus shelters, public parks, encroachment, and civic signs.",
        "keywords": [
            "footpath", "sidewalk", "pedestrian walkway", "bus shelter", "bus stop", "park",
            "public park", "bench", "benches", "signage", "board", "encroachment", "fence",
            "public toilet", "urinal", "community center", "railing", "boundary wall",
        ],
    },
}

# Category to Department Code rule mapping
CATEGORY_TO_DEPT_CODE = {
    "Road Infrastructure": "ROADS",
    "Water Supply": "WATER",
    "Sanitation": "SANITATION",
    "Drainage": "DRAINAGE",
    "Electricity and Streetlights": "ELECTRICAL",
    "Public Infrastructure": "PUBLIC_INFRA",
}


class DepartmentRouter:
    """
    Intelligent rules-based routing engine matching complaints to municipal departments.
    Combines structured category rules with text/keyword frequency analysis.
    """

    @classmethod
    def route(
        cls,
        category: Optional[str] = None,
        issue_type: Optional[str] = None,
        text: Optional[str] = None,
    ) -> DepartmentRoutingResult:
        """
        Routes grievance to appropriate municipal department with an explainable routing trace.
        """
        combined_text = f"{category or ''} {issue_type or ''} {text or ''}".lower()

        # Rule 1: Direct Category Mapping if supplied and recognized
        if category and category in CATEGORY_TO_DEPT_CODE:
            dept_code = CATEGORY_TO_DEPT_CODE[category]
            dept_info = DEPARTMENTS[dept_code]
            return DepartmentRoutingResult(
                department_code=dept_code,
                department_name=dept_info["name"],
                matched_rule=f"Category Rule: '{category}' → {dept_code}",
                routing_explanation=f"Routed directly to {dept_info['name']} based on standardized complaint category.",
                is_fallback=False,
            )

        # Rule 2: Multi-keyword density scoring across department dictionaries
        scores: Dict[str, Tuple[int, str]] = {}
        for code, info in DEPARTMENTS.items():
            matches = [kw for kw in info["keywords"] if re.search(r"\b" + re.escape(kw) + r"\b", combined_text)]
            if matches:
                scores[code] = (len(matches), ", ".join(matches[:3]))

        if scores:
            # Sort by keyword match count descending
            best_code, (match_count, sample_kws) = max(scores.items(), key=lambda item: item[1][0])
            dept_info = DEPARTMENTS[best_code]
            return DepartmentRoutingResult(
                department_code=best_code,
                department_name=dept_info["name"],
                matched_rule=f"Keyword Rule: matched {match_count} terms ({sample_kws})",
                routing_explanation=f"Routed to {dept_info['name']} based on keyword analysis indicating {sample_kws}.",
                is_fallback=False,
            )

        # Rule 3: Deterministic fallback when category is unspecified and keywords are ambiguous.
        # Unmatched grievances are NOT silently routed to ROADS; they are explicitly flagged
        # for administrative manual review.
        return DepartmentRoutingResult(
            department_code="PENDING_REVIEW",
            department_name="Pending Administrative Triage",
            matched_rule="Unmatched - Requires Manual Department Review",
            routing_explanation="Complaint could not be confidently mapped to a municipal department. Flagged for manual administrative review.",
            is_fallback=True,
            requires_manual_review=True,
        )
