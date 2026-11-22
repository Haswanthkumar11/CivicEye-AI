import json
import logging
import re
import asyncio
from typing import Optional, Dict, Any

from app.core.config import settings
from app.services.ai.schemas import GeminiExtractionResult

logger = logging.getLogger(__name__)

GEMINI_SYSTEM_PROMPT = """You are CivicEye AI, a Senior Municipal Infrastructure & Public Safety Analyst for India.
Analyze citizen complaint texts (which may include English, Telugu, or transliterated descriptions) and extract structured civic grievance intelligence.

Strictly respond with a single, valid JSON object matching this exact schema:
{
  "complaint_category": "Road Infrastructure | Water Supply | Sanitation | Drainage | Electricity and Streetlights | Public Infrastructure | Other",
  "issue_type": "<Specific problem type, e.g. Pothole / Road Cavity, Pipe Burst, Garbage Accumulation, Clogged Drain, Streetlight Outage, Broken Footpath>",
  "description_summary": "<One concise sentence summarizing the core physical defect and impact>",
  "detected_damage": "<Specific damage described, e.g. 2ft deep road cavity, murky tap water, exposed 240V wire>",
  "estimated_damage_level": <number between 0.0 and 100.0 representing physical severity>,
  "potential_public_risk": <number between 0.0 and 100.0 representing danger to life, injury, or public health>,
  "affected_public_groups": "<Primary impacted groups, e.g. Two-wheeler commuters, Schoolchildren, Local residents>",
  "estimated_public_impact": <number between 0.0 and 100.0 estimating citizen inconvenience, traffic congestion, and commuter disruption>,
  "location_sensitivity": <number between 0.0 and 100.0 based on crowd density or proximity to schools, hospitals, transit hubs, or arterial junctions, default 50.0>,
  "recommended_department": "ROADS | WATER | SANITATION | DRAINAGE | ELECTRICAL | PUBLIC_INFRA | PENDING_REVIEW",
  "confidence_score": <number between 0.0 and 1.0 representing model certainty>,
  "reasoning": "<Short analytical sentence explaining why this category and risk level were chosen>"
}

Do not include markdown code block markers (like ```json), commentary, or any text outside the raw JSON object.
"""


class GeminiService:
    """
    Client for Google Gemini multimodal API using the official Google GenAI Python SDK (`google-genai`).
    Enforces timeout, structured prompt assembly, JSON extraction, and validation.
    Avoids duplicate REST code paths and protects API keys from exposure in logs or responses.
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL or "gemini-2.0-flash"
        self.enabled = getattr(settings, "AI_ANALYSIS_ENABLED", True)
        self._client = None

    def is_available(self) -> bool:
        """Returns True if Gemini API key is configured and AI analysis is enabled."""
        if not self.enabled or not self.api_key:
            return False
        cleaned = self.api_key.strip()
        if not cleaned or cleaned == "your-google-gemini-api-key-here":
            return False
        return True

    def _get_client(self):
        """Lazily initializes the google-genai Client."""
        if self._client is None and self.is_available():
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    async def analyze_text(self, text: str, category_hint: Optional[str] = None) -> Optional[GeminiExtractionResult]:
        """
        Calls Gemini API using the official google-genai SDK to analyze grievance text.
        Returns validated GeminiExtractionResult or None on failure/unavailability.
        """
        if not self.is_available():
            logger.info("Gemini AI analysis skipped: GEMINI_API_KEY not configured or disabled.")
            return None

        prompt = f"Citizen Grievance Description:\n\"{text.strip()}\"\n"
        if category_hint:
            prompt += f"Citizen-Suggested Category: {category_hint}\n"
        prompt += "\nExtract structured civic complaint JSON now."

        try:
            from google.genai import types

            client = self._get_client()
            if not client:
                return None

            config = types.GenerateContentConfig(
                system_instruction=GEMINI_SYSTEM_PROMPT,
                temperature=0.1,
                response_mime_type="application/json",
            )

            # Strictly enforce 10-second async timeout
            response = await asyncio.wait_for(
                client.aio.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config,
                ),
                timeout=10.0,
            )

            raw_text = response.text if response else ""
            parsed = self._clean_and_parse_json(raw_text)
            if parsed:
                return GeminiExtractionResult(**parsed)

        except asyncio.TimeoutError:
            logger.warning(f"Gemini generation timed out after 10.0s for model {self.model_name}")
        except Exception as err:
            # Never expose API key in logs
            logger.warning(f"Gemini AI generation failed with model {self.model_name}: {type(err).__name__} - {str(err)[:150]}")

        return None

    def _clean_and_parse_json(self, raw: str) -> Optional[Dict[str, Any]]:
        """Cleans and extracts JSON object from raw response string."""
        if not raw:
            return None
        text = raw.strip()
        # Remove markdown code fences if present
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
        text = text.strip()

        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return self._normalize_extracted_dict(data)
        except Exception as e:
            # Try regex extraction of first {...}
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))
                    if isinstance(data, dict):
                        return self._normalize_extracted_dict(data)
                except Exception:
                    pass
            logger.warning(f"Could not parse valid JSON from Gemini output: {e}")
        return None

    def _normalize_extracted_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures all required fields exist and numbers are clamped into 0.0-100.0."""
        # Valid controlled departments
        valid_depts = {"ROADS", "WATER", "SANITATION", "DRAINAGE", "ELECTRICAL", "PUBLIC_INFRA", "PENDING_REVIEW"}
        dept = str(data.get("recommended_department", "PENDING_REVIEW")).upper().strip()
        if dept not in valid_depts:
            dept = "PENDING_REVIEW"

        # Valid categories
        valid_cats = {
            "Road Infrastructure", "Water Supply", "Sanitation",
            "Drainage", "Electricity and Streetlights", "Public Infrastructure", "Other"
        }
        cat = str(data.get("complaint_category", "Other")).strip()
        if cat not in valid_cats:
            cat = "Other"

        def _clamp(v: Any, default: float) -> float:
            try:
                val = float(v)
                return max(0.0, min(100.0, val))
            except Exception:
                return default

        def _clamp_unit(v: Any, default: float) -> float:
            try:
                val = float(v)
                return max(0.0, min(1.0, val))
            except Exception:
                return default

        return {
            "complaint_category": cat,
            "issue_type": str(data.get("issue_type", "Civic Defect")),
            "description_summary": str(data.get("description_summary", "Unspecified grievance summary")),
            "detected_damage": str(data.get("detected_damage", "Physical infrastructure damage")),
            "estimated_damage_level": _clamp(data.get("estimated_damage_level"), 50.0),
            "potential_public_risk": _clamp(data.get("potential_public_risk"), 50.0),
            "affected_public_groups": str(data.get("affected_public_groups", "Local residents & commuters")),
            "estimated_public_impact": _clamp(data.get("estimated_public_impact"), 50.0),
            "location_sensitivity": _clamp(data.get("location_sensitivity"), 50.0),
            "recommended_department": dept,
            "confidence_score": _clamp_unit(data.get("confidence_score"), 0.85),
            "reasoning": str(data.get("reasoning", "Classified via multimodal civic intelligence criteria.")),
        }
