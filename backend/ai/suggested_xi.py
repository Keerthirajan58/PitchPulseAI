"""
suggested_xi.py — AI-Powered Tactical Lineup Generator

Takes squad readiness data, opponent info, and match context, then uses
Gemini to recommend the optimal formation, Starting XI, bench, and
per-player tactical rationales.

This is the AI engine behind Prithvi's interactive pitch map
(suggested_xi_screen.dart).

Interface for Roshini:
    generate_suggested_xi(opponent: str, match_context: str,
                          available_squad: list[dict]) -> dict
"""

import json
import logging
import os
from typing import Dict, Any, List

from .gemini_client import generate_json

logger = logging.getLogger(__name__)


VALID_FORMATIONS = {"4-3-3", "4-4-2", "4-2-3-1", "3-5-2", "3-4-3", "5-3-2", "5-4-1"}


def _get_suggested_xi_prompts() -> tuple[str, str]:
    """Loads system and user prompts for Suggested XI."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompts_dir = os.path.join(base_dir, "prompts")

    with open(os.path.join(prompts_dir, "suggested_xi_system.txt"), "r") as f:
        system_prompt = f.read()
    with open(os.path.join(prompts_dir, "suggested_xi_user.txt"), "r") as f:
        user_prompt_template = f.read()

    return system_prompt, user_prompt_template


def generate_suggested_xi(
    opponent: str,
    match_context: str,
    available_squad: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generates the optimal Starting XI, formation, and tactical rationale.

    Args:
        opponent: Name of the opposing team (e.g., "Bayern Munich").
        match_context: e.g., "Away, Champions League Semi-Final".
        available_squad: List of player dicts, each with at minimum:
            {
                "id": "uuid",
                "name": "Vinícius Jr",
                "position": "FW",      # GK | DEF | MID | FW
                "readiness": 95,        # 0-100
                "form": "Excellent"     # "Excellent" | "Good" | "Average" | "Poor"
            }

    Returns:
        dict: {
            "best_formation": "4-3-3",
            "tactical_analysis": str,
            "starting_xi_ids": [11 IDs],
            "bench_ids": [remaining IDs],
            "player_rationales": {id: str, ...}
        }
    """
    # Normalize squad: Prithvi may send `risk` instead of `form`.
    # Convert risk score to a form string if form is absent.
    def _risk_to_form(risk: int) -> str:
        if risk <= 25: return "Excellent"
        if risk <= 45: return "Good"
        if risk <= 65: return "Average"
        return "Poor"

    normalized_squad = []
    for p in available_squad:
        player = dict(p)
        if "form" not in player:
            player["form"] = _risk_to_form(int(player.get("risk", 50)))
        normalized_squad.append(player)

    context = {
        "opponent": opponent,
        "match_context": match_context,
        "available_squad": normalized_squad
    }

    try:
        system_prompt, user_prompt_template = _get_suggested_xi_prompts()
        user_prompt = user_prompt_template.format(context=json.dumps(context, indent=2))

        result = generate_json(system_prompt=system_prompt, user_prompt=user_prompt)

        # ── Validate result ──
        required_keys = {"best_formation", "tactical_analysis", "starting_xi_ids", "bench_ids", "player_rationales"}
        if not required_keys.issubset(result.keys()):
            missing = required_keys - set(result.keys())
            logger.warning(f"Gemini response missing keys: {missing}. Using fallback.")
            raise ValueError(f"Incomplete response, missing: {missing}")

        # Validate formation
        if result["best_formation"] not in VALID_FORMATIONS:
            logger.warning(f"Invalid formation '{result['best_formation']}', defaulting to 4-3-3.")
            result["best_formation"] = "4-3-3"

        # Validate Starting XI count
        if len(result["starting_xi_ids"]) != 11:
            logger.warning(f"Starting XI has {len(result['starting_xi_ids'])} players, expected 11. Using fallback.")
            raise ValueError("Starting XI must have exactly 11 players.")

        return result

    except Exception as e:
        logger.error(f"Suggested XI generation failed: {e}")
        return _fallback_xi(normalized_squad)


def _fallback_xi(squad: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Deterministic fallback: sorts by readiness and picks the top 11 for a 4-3-3.
    Ensures at least 1 GK, 4 DEF, 3 MID, 3 FW.
    """
    # Group by position
    gks = sorted([p for p in squad if p.get("position") == "GK"], key=lambda x: x.get("readiness", 0), reverse=True)
    defs = sorted([p for p in squad if p.get("position") == "DEF"], key=lambda x: x.get("readiness", 0), reverse=True)
    mids = sorted([p for p in squad if p.get("position") == "MID"], key=lambda x: x.get("readiness", 0), reverse=True)
    fws = sorted([p for p in squad if p.get("position") == "FW"], key=lambda x: x.get("readiness", 0), reverse=True)

    xi = []
    xi += [p["id"] for p in gks[:1]]
    xi += [p["id"] for p in defs[:4]]
    xi += [p["id"] for p in mids[:3]]
    xi += [p["id"] for p in fws[:3]]

    # If we don't have enough for 11, fill from highest readiness overall
    if len(xi) < 11:
        remaining = sorted(
            [p for p in squad if p["id"] not in xi],
            key=lambda x: x.get("readiness", 0),
            reverse=True
        )
        xi += [p["id"] for p in remaining[:11 - len(xi)]]

    all_ids = {p["id"] for p in squad}
    bench = list(all_ids - set(xi))

    rationales = {}
    for pid in xi:
        player = next((p for p in squad if p["id"] == pid), None)
        if player:
            rationales[pid] = f"{player['name']} selected — Readiness: {player.get('readiness', '?')}%, Form: {player.get('form', 'N/A')}, Risk: {player.get('risk', 'N/A')}."

    return {
        "best_formation": "4-3-3",
        "tactical_analysis": "Fallback selection: top readiness players selected in a balanced 4-3-3 formation.",
        "starting_xi_ids": xi[:11],
        "bench_ids": bench,
        "player_rationales": rationales
    }
