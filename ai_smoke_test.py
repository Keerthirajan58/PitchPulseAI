import json
import logging
import os
from dotenv import load_dotenv

load_dotenv()

from backend.ai.action_plan import generate_action_plan
from backend.ai.match_report import generate_match_report
from backend.ai.presage_readiness import process_presage_checkin
from backend.ai.suggested_xi import generate_suggested_xi

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)



def test_action_plan():
    logger.info("=" * 60)
    logger.info("TEST 2: Action Plan (Gemini + RAG)")
    logger.info("=" * 60)

    player_context = {
        "name": "Vinicius Jr",
        "position": "Winger",
        "metrics_this_week": {
            "risk_score": 85,
            "readiness_score": 35,
            "drivers": ["Sprint distance +25% vs baseline", "Low sleep quality reported"]
        },
        "last_match": {"minutes": 95, "high_speed_running_m": 1200}
    }

    plan = generate_action_plan(player_context)
    logger.info(f"Generated Action Plan JSON:\n{json.dumps(plan, indent=2)}")

    # Validate required keys
    for key in ["summary", "why", "recommendations", "caution"]:
        assert key in plan, f"Missing key: {key}"
    logger.info("✅ Action Plan Test: PASSED\n")


def test_match_report():
    logger.info("=" * 60)
    logger.info("TEST 3: Match Report")
    logger.info("=" * 60)

    fixture = {"opponent": "Barcelona", "result": "Real Madrid 2 - 1 Barcelona", "intensity_rating": "Very High"}
    team_stats = {"total_distance_km": 115, "avg_possession": "45%"}
    player_load = [
        {"name": "Valverde", "minutes": 90, "load_flag": "High (ACWR approaching 1.5)"},
        {"name": "Modric", "minutes": 65, "load_flag": "Normal"}
    ]

    report = generate_match_report(fixture, team_stats, player_load)
    logger.info(f"Generated Match Report JSON:\n{json.dumps(report, indent=2)}")

    for key in ["match_summary", "squad_load_assessment", "critical_flags"]:
        assert key in report, f"Missing key: {key}"
    logger.info("✅ Match Report Test: PASSED\n")


def test_presage_checkin():
    logger.info("=" * 60)
    logger.info("TEST 4: Presage Selfie Check-In")
    logger.info("=" * 60)

    player_context = {
        "name": "Jude Bellingham",
        "position": "Central Midfielder",
        "risk_score": 72,
        "readiness_score": 55,
        "acwr": 1.4,
        "last_match_minutes": 90,
        "baselines": {"resting_pulse_rate": 58, "hrv_ms": 72, "breathing_rate": 13}
    }

    # Scenario: Fatigued player — elevated HR, suppressed HRV, high emotional stress
    vitals = {
        "pulse_rate": 78,
        "hrv_ms": 38,
        "breathing_rate": 19,
        "stress_level": "High",
        "focus": "Low",
        "valence": "Negative",
        "confidence": 0.88
    }

    result = process_presage_checkin(player_context, vitals)
    logger.info(f"Presage Check-In Result:\n{json.dumps(result, indent=2)}")

    for key in ["readiness_delta", "readiness_flag", "emotional_state", "contributing_factors", "recommendation"]:
        assert key in result, f"Missing key: {key}"
    assert result["readiness_flag"] in ["GOOD", "CONCERN", "ALERT"], f"Invalid flag: {result['readiness_flag']}"
    assert -15 <= result["readiness_delta"] <= 10, f"Delta out of range: {result['readiness_delta']}"
    logger.info("✅ Presage Check-In Test: PASSED\n")



def test_suggested_xi():
    logger.info("=" * 60)
    logger.info("TEST 6: Suggested XI (Tactical Lineup)")
    logger.info("=" * 60)

    squad = [
        {"id": "p1",  "name": "Courtois",    "position": "GK",  "readiness": 92, "form": "Excellent"},
        {"id": "p2",  "name": "Carvajal",    "position": "DEF", "readiness": 78, "form": "Good"},
        {"id": "p3",  "name": "Militão",     "position": "DEF", "readiness": 85, "form": "Good"},
        {"id": "p4",  "name": "Rüdiger",     "position": "DEF", "readiness": 88, "form": "Excellent"},
        {"id": "p5",  "name": "Mendy",       "position": "DEF", "readiness": 70, "form": "Average"},
        {"id": "p6",  "name": "Tchouaméni",  "position": "MID", "readiness": 82, "form": "Good"},
        {"id": "p7",  "name": "Bellingham",  "position": "MID", "readiness": 91, "form": "Excellent"},
        {"id": "p8",  "name": "Valverde",    "position": "MID", "readiness": 65, "form": "Average"},
        {"id": "p9",  "name": "Vinícius Jr", "position": "FW",  "readiness": 95, "form": "Excellent"},
        {"id": "p10", "name": "Mbappé",      "position": "FW",  "readiness": 90, "form": "Good"},
        {"id": "p11", "name": "Rodrygo",     "position": "FW",  "readiness": 84, "form": "Good"},
        {"id": "p12", "name": "Modric",      "position": "MID", "readiness": 60, "form": "Average"},
        {"id": "p13", "name": "Camavinga",   "position": "MID", "readiness": 88, "form": "Good"},
        {"id": "p14", "name": "Nacho",       "position": "DEF", "readiness": 72, "form": "Average"},
        {"id": "p15", "name": "Lunin",       "position": "GK",  "readiness": 80, "form": "Good"},
    ]

    result = generate_suggested_xi(
        opponent="Bayern Munich",
        match_context="Away, Champions League Semi-Final",
        available_squad=squad
    )
    logger.info(f"Suggested XI Result:\n{json.dumps(result, indent=2)}")

    # Validate structure
    for key in ["best_formation", "tactical_analysis", "starting_xi_ids", "bench_ids", "player_rationales"]:
        assert key in result, f"Missing key: {key}"
    assert len(result["starting_xi_ids"]) == 11, f"Expected 11 starters, got {len(result['starting_xi_ids'])}"
    assert result["best_formation"] in {"4-3-3", "4-4-2", "4-2-3-1", "3-5-2", "3-4-3", "5-3-2", "5-4-1"}
    logger.info("✅ Suggested XI Test: PASSED\n")


if __name__ == "__main__":
    if not os.environ.get("GEMINI_API_KEY"):
        logger.warning("No GEMINI_API_KEY found. Skipping real API calls.")
    else:
        test_action_plan()
        test_match_report()
        test_presage_checkin()
        test_suggested_xi()

        logger.info("=" * 60)
        logger.info("🏆 ALL 4 TESTS PASSED SUCCESSFULLY!")
        logger.info("=" * 60)
