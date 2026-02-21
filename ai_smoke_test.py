import json
import logging
import os
from dotenv import load_dotenv

load_dotenv()

from backend.ai.embeddings import embed_text, create_player_week_document
from backend.ai.action_plan import generate_action_plan
from backend.ai.match_report import generate_match_report
from backend.ai.presage_readiness import process_presage_checkin
from backend.ai.vector_db import seed_knowledge_base, upsert_player_week, search_similar_cases

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def test_embeddings():
    logger.info("=" * 60)
    logger.info("TEST 1: Embeddings")
    logger.info("=" * 60)

    doc = create_player_week_document(
        player_name="Jude Bellingham",
        week_start="2023-10-23",
        risk_score=72.5,
        readiness=45.0,
        acwr=1.65,
        monotony=2.1,
        strain=3.4,
        last_match_minutes=90,
        drivers=["High ACWR spike", "3 consecutive 90min matches"],
        recommended_action="Cap training minutes, monitor hamstring."
    )

    logger.info(f"Canonical Doc:\n{doc}")

    vec = embed_text(doc)
    logger.info(f"Embedding generated. Dimension: {len(vec)}")
    assert len(vec) == 3072, f"Expected 3072-dim, got {len(vec)}"
    logger.info("✅ Embedding Test: PASSED\n")


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

    retrieved_cases = [
        {
            "context_data": {"risk_score": 82, "drivers": ["Sprint distance +20%"]},
            "outcome": "Player suffered Grade 1 hamstring strain next match."
        }
    ]

    retrieved_playbook = [
        "Winger Protocol: If Sprint Distance exceeds baseline by 20%+, limit MD-2 drills."
    ]

    plan = generate_action_plan(player_context, retrieved_cases, retrieved_playbook)
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

    # Scenario: Fatigued player — elevated HR, suppressed HRV
    vitals = {
        "pulse_rate": 78,
        "hrv_ms": 38,
        "breathing_rate": 19,
        "confidence": 0.88
    }

    result = process_presage_checkin(player_context, vitals)
    logger.info(f"Presage Check-In Result:\n{json.dumps(result, indent=2)}")

    for key in ["readiness_delta", "readiness_flag", "contributing_factors", "recommendation"]:
        assert key in result, f"Missing key: {key}"
    assert result["readiness_flag"] in ["GOOD", "CONCERN", "ALERT"], f"Invalid flag: {result['readiness_flag']}"
    assert -15 <= result["readiness_delta"] <= 10, f"Delta out of range: {result['readiness_delta']}"
    logger.info("✅ Presage Check-In Test: PASSED\n")


def test_vector_db():
    logger.info("=" * 60)
    logger.info("TEST 5: Actian VectorAI DB (Seed + Search)")
    logger.info("=" * 60)

    # Seed the knowledge base
    count = seed_knowledge_base()
    logger.info(f"Seeded {count} documents into vector DB.")
    assert count > 0, "No documents seeded"

    # Upsert a player-week
    doc = create_player_week_document(
        player_name="Test Player",
        week_start="2026-02-10",
        risk_score=80,
        readiness=40,
        acwr=1.55,
        monotony=2.0,
        strain=1400,
        last_match_minutes=90,
        drivers=["High ACWR", "Fixture congestion"],
        recommended_action="Reduce training load."
    )
    upsert_player_week(
        player_id="test-uuid-123",
        player_name="Test Player",
        week="2026-02-10T00:00:00",
        doc_text=doc,
        metadata={"acwr": 1.55, "risk_score": 80}
    )
    logger.info("Upserted test player-week.")

    # Search for similar cases
    query = create_player_week_document(
        player_name="Query Player",
        week_start="2026-02-17",
        risk_score=78,
        readiness=42,
        acwr=1.60,
        monotony=1.9,
        strain=1300,
        last_match_minutes=88,
        drivers=["Sprint overload", "3 matches in 8 days"],
        recommended_action="Rest day needed."
    )
    results = search_similar_cases(query, k=3)
    logger.info(f"Similar Cases Found: {len(results)}")
    for r in results:
        logger.info(f"  → {r['player_name']} (score: {r['similarity_score']}) — {r['summary'][:80]}...")

    assert len(results) > 0, "No similar cases returned"

    # Validate result format matches Prithvi's Flutter model
    for r in results:
        for key in ["player_id", "player_name", "week_label", "similarity_score", "summary", "outcome"]:
            assert key in r, f"Missing key in result: {key}"

    logger.info("✅ Vector DB Test: PASSED\n")


if __name__ == "__main__":
    if not os.environ.get("GEMINI_API_KEY"):
        logger.warning("No GEMINI_API_KEY found. Skipping real API calls.")
    else:
        test_embeddings()
        test_action_plan()
        test_match_report()
        test_presage_checkin()
        test_vector_db()

        logger.info("=" * 60)
        logger.info("🏆 ALL 5 TESTS PASSED SUCCESSFULLY!")
        logger.info("=" * 60)
