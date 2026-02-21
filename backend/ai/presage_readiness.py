"""
presage_readiness.py — Presage SmartSpectra SDK Vitals Fusion Module

Receives contactless camera-based vitals from Presage (pulse rate, HRV,
breathing rate, confidence) captured via the Flutter app's selfie check-in.
Fuses these signals with the player's current workload context and uses
Gemini to produce a structured readiness adjustment.

Interface for Roshini:
    process_presage_checkin(player_context: dict, vitals: dict) -> dict
"""

import json
import logging
import os
from typing import Dict, Any

from .gemini_client import generate_json

logger = logging.getLogger(__name__)


# ─── BASELINE THRESHOLDS ────────────────────────────────────────────────────────
# These defaults are used when the player's personal baseline is not available.
# In a production system, baselines would be computed per-player over 28 days.

DEFAULT_BASELINES = {
    "resting_pulse_rate": 62,   # bpm (elite soccer player average)
    "hrv_ms": 65,               # ms (RMSSD, elite athlete average)
    "breathing_rate": 14,       # breaths per minute at rest
}


def _compute_heuristic_delta(vitals: Dict[str, Any], baselines: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes a rule-based readiness delta BEFORE sending to Gemini.
    This ensures we have deterministic fallback values even if Gemini fails.
    """
    delta = 0.0
    flag = "GOOD"
    factors = []

    pulse = vitals.get("pulse_rate", 0)
    hrv = vitals.get("hrv_ms", 0)
    breathing = vitals.get("breathing_rate", 0)
    confidence = vitals.get("confidence", 0.0)

    baseline_pulse = baselines.get("resting_pulse_rate", DEFAULT_BASELINES["resting_pulse_rate"])
    baseline_hrv = baselines.get("hrv_ms", DEFAULT_BASELINES["hrv_ms"])
    baseline_breathing = baselines.get("breathing_rate", DEFAULT_BASELINES["breathing_rate"])

    # ── Pulse Rate Analysis ──
    if pulse > 0:
        pulse_diff = pulse - baseline_pulse
        if pulse_diff > 20:
            delta -= 10
            flag = "ALERT"
            factors.append(f"Resting HR elevated +{pulse_diff}bpm above baseline ({baseline_pulse}bpm)")
        elif pulse_diff > 10:
            delta -= 5
            if flag != "ALERT":
                flag = "CONCERN"
            factors.append(f"Resting HR moderately elevated +{pulse_diff}bpm above baseline ({baseline_pulse}bpm)")
        elif pulse_diff < -5:
            delta += 3
            factors.append(f"Resting HR well below baseline (indicates good recovery)")

    # ── HRV Analysis ──
    if hrv > 0 and baseline_hrv > 0:
        hrv_ratio = hrv / baseline_hrv
        if hrv_ratio < 0.5:
            delta -= 8
            flag = "ALERT"
            factors.append(f"HRV severely suppressed at {hrv}ms ({int(hrv_ratio*100)}% of baseline {baseline_hrv}ms)")
        elif hrv_ratio < 0.7:
            delta -= 4
            if flag != "ALERT":
                flag = "CONCERN"
            factors.append(f"HRV suppressed at {hrv}ms ({int(hrv_ratio*100)}% of baseline {baseline_hrv}ms)")
        elif hrv_ratio > 1.1:
            delta += 3
            factors.append(f"HRV elevated at {hrv}ms (indicates parasympathetic recovery)")

    # ── Breathing Rate Analysis ──
    if breathing > 20:
        delta -= 3
        if flag == "GOOD":
            flag = "CONCERN"
        factors.append(f"Breathing rate elevated at {breathing} breaths/min (resting expected ~{baseline_breathing})")

    # ── Confidence Check ──
    if confidence < 0.5:
        if flag == "GOOD":
            flag = "CONCERN"
        factors.append(f"Presage measurement confidence low ({confidence:.2f}). Recommend re-check in better lighting.")

    # Clamp delta
    delta = max(-15.0, min(10.0, delta))

    if not factors:
        factors.append("All vitals within normal range. Player appears well-recovered.")

    return {
        "readiness_delta": round(delta, 1),
        "readiness_flag": flag,
        "contributing_factors": factors[:3],  # Max 3 factors
        "recommendation": ""  # Will be filled by Gemini
    }


def _get_presage_prompts() -> tuple[str, str]:
    """Loads the Presage system and user prompts."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompts_dir = os.path.join(base_dir, "prompts")

    with open(os.path.join(prompts_dir, "presage_system.txt"), "r") as f:
        system_prompt = f.read()
    with open(os.path.join(prompts_dir, "presage_user.txt"), "r") as f:
        user_prompt_template = f.read()

    return system_prompt, user_prompt_template


def process_presage_checkin(player_context: Dict[str, Any], vitals: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processes a Presage camera-based selfie check-in for a player.

    Args:
        player_context: The player's current state, e.g.:
            {
                "name": "Vinicius Jr",
                "position": "Winger",
                "risk_score": 72,
                "readiness_score": 55,
                "acwr": 1.4,
                "last_match_minutes": 90,
                "baselines": {"resting_pulse_rate": 58, "hrv_ms": 72, "breathing_rate": 13}
            }
        vitals: The raw vitals from Presage SmartSpectra SDK:
            {
                "pulse_rate": 74,
                "hrv_ms": 42,
                "breathing_rate": 18,
                "confidence": 0.88
            }

    Returns:
        dict: {
            "readiness_delta": float (-15 to +10),
            "readiness_flag": "GOOD" | "CONCERN" | "ALERT",
            "contributing_factors": [str, str, str],
            "recommendation": str
        }
    """
    # Step 1: Get player baselines (use defaults if not provided)
    baselines = player_context.get("baselines", DEFAULT_BASELINES)

    # Step 2: Compute heuristic delta as a deterministic fallback
    heuristic = _compute_heuristic_delta(vitals, baselines)

    # Step 3: Build context for Gemini to generate the recommendation
    context = {
        "player": {
            "name": player_context.get("name", "Unknown"),
            "position": player_context.get("position", "Unknown"),
            "current_risk_score": player_context.get("risk_score", 50),
            "current_readiness_score": player_context.get("readiness_score", 50),
            "acwr": player_context.get("acwr", 1.0),
            "last_match_minutes": player_context.get("last_match_minutes", 0),
        },
        "presage_vitals": vitals,
        "baselines": baselines,
        "heuristic_assessment": {
            "readiness_delta": heuristic["readiness_delta"],
            "readiness_flag": heuristic["readiness_flag"],
            "contributing_factors": heuristic["contributing_factors"],
        }
    }

    # Step 4: Call Gemini for the enriched assessment + recommendation
    try:
        system_prompt, user_prompt_template = _get_presage_prompts()
        user_prompt = user_prompt_template.format(context=json.dumps(context, indent=2))
        result = generate_json(system_prompt=system_prompt, user_prompt=user_prompt)

        # Validate required keys exist in Gemini response
        required_keys = {"readiness_delta", "readiness_flag", "contributing_factors", "recommendation"}
        if not required_keys.issubset(result.keys()):
            logger.warning("Gemini response missing keys, falling back to heuristic.")
            raise ValueError("Incomplete Gemini response")

        return result

    except Exception as e:
        logger.warning(f"Gemini enrichment failed ({e}), using heuristic fallback.")
        # Use the heuristic result with a generic recommendation
        if heuristic["readiness_flag"] == "ALERT":
            heuristic["recommendation"] = "Escalate to medical staff. Do not include in high-intensity training today."
        elif heuristic["readiness_flag"] == "CONCERN":
            heuristic["recommendation"] = "Monitor closely. Reduce training load by 20% and re-assess before match day."
        else:
            heuristic["recommendation"] = "Player cleared for full training. No readiness concerns detected."
        return heuristic
