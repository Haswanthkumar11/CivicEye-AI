import json
import logging
import re
from typing import Optional, Dict, Any
import httpx

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
  "location_sensitivity": <number between 0.0 and 100.0 based on crowd density or traffic sensitivity hinted in text, default 50.0>,
  "recommended_department": "ROADS | WATER | SANITATION | DRAINAGE | ELECTRICAL | PUBLIC_INFRA",
  "confidence_score": <number between 0.0 and 1.0 representing model certainty>,
  "reasoning": "<Short analytical sentence explaining why this category and risk level were chosen>"
}

Do not include markdown code block markers (like ```json), commentary, or any text outside the raw JSON object.
"""


class GeminiService:
    """
    Client for Google Gemini multimodal API.
    Handles structured prompt assembly, timeout enforcement, JSON extraction, and validation.
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL or "gemini-1.5-flash"
        self.enabled = getattr(settings, "AI_ANALYSIS_ENABLED", True)

    def is_available(self) -> bool:
        """Returns True if Gemini API key is configured and AI analysis is enabled."""
        return bool(self.enabled and self.api_key and self.api_key.strip() and self.api_key != "your-google-gemini-api-key-here")

    async def analyze_text(self, text: str, category_hint: Optional[str] = None) -> Optional[GeminiExtractionResult]:
        """
        Calls Gemini API to analyze grievance text.
        Returns validated GeminiExtractionResult or None on failure/unavailability.
        """
        if not self.is_available():
            logger.info("Gemini AI analysis skipped: GEMINI_API_KEY not configured or disabled.")
            return None

        prompt = f"Citizen Grievance Description:\n\"{text.strip()}\"\n"
        if category_hint:
            prompt += f"Citizen-Suggested Category: {category_hint}\n"
        prompt += "\nExtract structured civic complaint JSON now."

        # Attempt 1: Using google.generativeai SDK if available
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=GEMINI_SYSTEM_PROMPT,
                generation_config={"temperature": 0.1, "response_mime_type": "application/json"},
            )
            response = await model.generate_content_async(prompt)
            raw_text = response.text if response else ""
            parsed = self._clean_and_parse_json(raw_text)
            if parsed:
                return GeminiExtractionResult(**parsed)
        except Exception as sdk_err:
            logger.warning(f"Gemini SDK generation failed, attempting REST API fallback: {sdk_err}")

        # Attempt 2: Direct REST fallback via httpx (timeout: 10s)
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": f"{GEMINI_SYSTEM_PROMPT}\n\n{prompt}"}]}],
                "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"},
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            raw_text = parts[0].get("text", "")
                            parsed = self._clean_and_parse_json(raw_text)
                            if parsed:
                                return GeminiExtractionResult(**parsed)
                else:
                    logger.error(f"Gemini REST returned status {res.status_code}: {res.text[:200]}")
        except Exception as rest_err:
            logger.error(f"Gemini REST call encountered error: {rest_err}")

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
                # Normalize values
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
        valid_depts = {"ROADS", "WATER", "SANITATION", "DRAINAGE", "ELECTRICAL", "PUBLIC_INFRA"}
        dept = str(data.get("recommended_department", "ROADS")).upper().strip()
        if dept not in valid_depts:
            dept = "ROADS"

        # Valid categories
        valid_cats = {
            "Road Infrastructure", "Water Supply", "Sanitation",
            "Drainage", "Electricity and Streetlights", "Public Infrastructure", "Other"
        }
        cat = str(data.get("complaint_category", "Road Infrastructure")).strip()
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
            "location_sensitivity": _clamp(data.get("location_sensitivity"), 50.0),
            "recommended_department": dept,
            "confidence_score": _clamp_unit(data.get("confidence_score"), 0.85),
            "reasoning": str(data.get("reasoning", "Classified via multimodal civic intelligence criteria.")),
        }
