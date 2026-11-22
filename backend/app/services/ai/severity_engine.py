import math
from typing import Optional, Tuple
from app.services.ai.schemas import SeverityFactorBreakdown


# Weight constants strictly matching CivicEye AI architecture specification
WEIGHT_DAMAGE = 0.30
WEIGHT_RISK = 0.30
WEIGHT_PUBLIC_IMPACT = 0.20
WEIGHT_LOCATION_SENSITIVITY = 0.20

# Standard priority boundary thresholds
THRESHOLD_LOW_MAX = 30.0
THRESHOLD_MEDIUM_MAX = 60.0
THRESHOLD_HIGH_MAX = 80.0


def clamp_factor(value: Optional[float], default: float = 50.0) -> float:
    """
    Validates, handles missing/NaN inputs, and strictly clamps factor values between 0.0 and 100.0.
    """
    if value is None:
        return default
    try:
        f_val = float(value)
        if math.isnan(f_val) or math.isinf(f_val):
            return default
        return max(0.0, min(100.0, f_val))
    except (ValueError, TypeError):
        return default


def get_severity_level(score: float) -> str:
    """
    Maps a continuous severity score to one of the four standardized priority tiers:
      - LOW: 0.0 <= score <= 30.0
      - MEDIUM: 30.0 < score <= 60.0
      - HIGH: 60.0 < score <= 80.0
      - CRITICAL: 80.0 < score <= 100.0
    """
    if score <= THRESHOLD_LOW_MAX:
        return "LOW"
    elif score <= THRESHOLD_MEDIUM_MAX:
        return "MEDIUM"
    elif score <= THRESHOLD_HIGH_MAX:
        return "HIGH"
    else:
        return "CRITICAL"


class SeverityEngine:
    """
    Deterministic explainable priority calculation engine.
    Ensures that AI estimates the raw factors, but Python calculates the final score mathematically.
    """

    @classmethod
    def calculate(
        cls,
        damage_factor: Optional[float] = 50.0,
        risk_factor: Optional[float] = 50.0,
        public_impact_factor: Optional[float] = 50.0,
        location_sensitivity_factor: Optional[float] = 50.0,
    ) -> SeverityFactorBreakdown:
        """
        Calculates deterministic priority score using the formula:
        S = 0.30 * Damage + 0.30 * Risk + 0.20 * Public Impact + 0.20 * Location Sensitivity
        """
        # Clamp each input factor strictly into [0.0, 100.0]
        c_damage = clamp_factor(damage_factor, default=50.0)
        c_risk = clamp_factor(risk_factor, default=50.0)
        c_impact = clamp_factor(public_impact_factor, default=50.0)
        c_sensitivity = clamp_factor(location_sensitivity_factor, default=50.0)

        # Compute weighted sum
        raw_score = (
            WEIGHT_DAMAGE * c_damage
            + WEIGHT_RISK * c_risk
            + WEIGHT_PUBLIC_IMPACT * c_impact
            + WEIGHT_LOCATION_SENSITIVITY * c_sensitivity
        )

        # Clamp and round final score to two decimal places
        final_score = round(max(0.0, min(100.0, raw_score)), 2)
        severity_level = get_severity_level(final_score)

        explanation = (
            f"Deterministic Score = {final_score}/100 ({severity_level}). "
            f"Factors: Damage ({c_damage:.1f} × 0.30 = {c_damage * WEIGHT_DAMAGE:.2f}), "
            f"Safety Risk ({c_risk:.1f} × 0.30 = {c_risk * WEIGHT_RISK:.2f}), "
            f"Public Impact ({c_impact:.1f} × 0.20 = {c_impact * WEIGHT_PUBLIC_IMPACT:.2f}), "
            f"Location Sensitivity ({c_sensitivity:.1f} × 0.20 = {c_sensitivity * WEIGHT_LOCATION_SENSITIVITY:.2f})."
        )

        return SeverityFactorBreakdown(
            damage_factor=round(c_damage, 2),
            risk_factor=round(c_risk, 2),
            public_impact_factor=round(c_impact, 2),
            location_sensitivity_factor=round(c_sensitivity, 2),
            final_score=final_score,
            severity_level=severity_level,
            formula=f"{WEIGHT_DAMAGE}*Damage + {WEIGHT_RISK}*Risk + {WEIGHT_PUBLIC_IMPACT}*Impact + {WEIGHT_LOCATION_SENSITIVITY}*Sensitivity",
            calculation_explanation=explanation,
        )
