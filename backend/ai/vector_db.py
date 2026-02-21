"""
vector_db.py — Actian VectorAI DB Integration Wrapper

Provides a clean interface for the PitchPulse backend to:
  1. Seed the knowledge base (playbook rules + historical case studies)
  2. Upsert player-week embeddings after match processing
  3. Search for similar cases (RAG retrieval for action plans)

Uses the Actian CortexClient (gRPC on port 50051) when VECTOR_DB_URL is set.
Falls back to a simple in-memory store for local development / demo mode.

Interface for Roshini:
    seed_knowledge_base() -> int
    upsert_player_week(player_id, week, doc_text, metadata) -> None
    search_similar_cases(query_text, k=5) -> list[dict]
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional

from .embeddings import embed_text

logger = logging.getLogger(__name__)

# ─── COLLECTION CONSTANTS ────────────────────────────────────────────────────
COLLECTION_NAME = "pitchpulse_vectors"
VECTOR_DIMENSION = 3072  # gemini-embedding-001 output dimension


# ─── IN-MEMORY FALLBACK ─────────────────────────────────────────────────────
# Used when Actian is not available (local dev, demo mode)

class LocalFallbackVectorStore:
    """Simple in-memory vector store for development/demo without Actian."""

    def __init__(self):
        self._vectors: Dict[int, Dict[str, Any]] = {}  # id -> {vector, payload}
        self._next_id = 0
        logger.info("Using LocalFallbackVectorStore (in-memory). Set VECTOR_DB_URL to use Actian.")

    def upsert(self, doc_id: int, vector: List[float], payload: Dict[str, Any]):
        self._vectors[doc_id] = {"vector": vector, "payload": payload}

    def batch_upsert(self, ids: List[int], vectors: List[List[float]], payloads: List[Dict[str, Any]]):
        for doc_id, vec, pay in zip(ids, vectors, payloads):
            self._vectors[doc_id] = {"vector": vec, "payload": pay}

    def search(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Cosine similarity search over in-memory vectors."""
        if not self._vectors:
            return []

        results = []
        for doc_id, entry in self._vectors.items():
            score = _cosine_similarity(query_vector, entry["vector"])
            results.append({"id": doc_id, "score": score, "payload": entry["payload"]})

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    @property
    def count(self) -> int:
        return len(self._vectors)


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Computes cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = sum(x * x for x in a) ** 0.5
    mag_b = sum(x * x for x in b) ** 0.5
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# ─── CLIENT INITIALIZATION ──────────────────────────────────────────────────

_client = None
_is_actian = False


def _get_client():
    """Returns the vector DB client (Actian CortexClient or in-memory fallback)."""
    global _client, _is_actian

    if _client is not None:
        return _client

    vector_db_url = os.environ.get("VECTOR_DB_URL", "").strip()

    if vector_db_url:
        try:
            from cortex import CortexClient, DistanceMetric
            _client = CortexClient(vector_db_url)
            # Health check
            version, uptime = _client.health_check()
            logger.info(f"Connected to Actian VectorAI DB: {version} (uptime: {uptime})")

            # Ensure collection exists
            try:
                _client.create_collection(
                    name=COLLECTION_NAME,
                    dimension=VECTOR_DIMENSION,
                    distance_metric=DistanceMetric.COSINE,
                )
                logger.info(f"Created Actian collection '{COLLECTION_NAME}' ({VECTOR_DIMENSION}-dim, COSINE)")
            except Exception:
                # Collection likely already exists
                logger.info(f"Actian collection '{COLLECTION_NAME}' already exists.")

            _is_actian = True
            return _client

        except ImportError:
            logger.warning("actiancortex package not installed. Falling back to in-memory store.")
        except Exception as e:
            logger.warning(f"Could not connect to Actian VectorAI ({e}). Falling back to in-memory store.")

    # Fallback
    _client = LocalFallbackVectorStore()
    _is_actian = False
    return _client


# ─── PUBLIC API ──────────────────────────────────────────────────────────────

_seed_counter = 0  # Global ID counter for seeded documents


def seed_knowledge_base() -> int:
    """
    Bulk-loads the knowledge_base_seed.json (playbook rules + historical cases)
    into the vector DB as embeddings.

    Returns:
        int: Number of documents seeded.
    """
    global _seed_counter
    client = _get_client()

    seed_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base_seed.json")
    with open(seed_file, "r") as f:
        seed_data = json.load(f)

    ids = []
    vectors = []
    payloads = []

    # Seed playbook rules
    for rule in seed_data.get("playbook_rules", []):
        doc_text = f"Playbook Rule: {rule['topic']}. {rule['rule_text']}"
        vec = embed_text(doc_text)
        ids.append(_seed_counter)
        vectors.append(vec)
        payloads.append({
            "source": rule.get("source", "PitchPulse_Playbook"),
            "topic": rule.get("topic", ""),
            "doc_type": "playbook_rule",
            "text": doc_text,
        })
        _seed_counter += 1

    # Seed historical cases
    for case in seed_data.get("historical_cases", []):
        ctx = case.get("context_data", {})
        doc_text = (
            f"Historical Case: {case['topic']}. "
            f"Position: {ctx.get('position', 'Unknown')}. "
            f"Risk: {ctx.get('risk_score', 0)}, Readiness: {ctx.get('readiness_score', 0)}. "
            f"ACWR: {ctx.get('acwr', 0)}, Monotony: {ctx.get('monotony', 0)}. "
            f"Drivers: {', '.join(ctx.get('drivers', []))}. "
            f"Intervention: {case.get('intervention', 'None')}. "
            f"Outcome: {case.get('outcome', 'Unknown')}."
        )
        vec = embed_text(doc_text)
        ids.append(_seed_counter)
        vectors.append(vec)
        payloads.append({
            "source": case.get("source", "PitchPulse_CaseStudy"),
            "topic": case.get("topic", ""),
            "doc_type": "historical_case",
            "text": doc_text,
            "outcome": case.get("outcome", ""),
            "intervention": case.get("intervention", ""),
        })
        _seed_counter += 1

    # Batch upsert
    if _is_actian:
        client.batch_upsert(COLLECTION_NAME, ids=ids, vectors=vectors, payloads=payloads)
    else:
        client.batch_upsert(ids=ids, vectors=vectors, payloads=payloads)

    logger.info(f"Seeded {len(ids)} documents into vector DB.")
    return len(ids)


def upsert_player_week(player_id: str, player_name: str, week: str,
                       doc_text: str, metadata: Dict[str, Any]) -> None:
    """
    Embeds and upserts a single player-week document into the vector DB.

    Args:
        player_id: UUID string of the player.
        player_name: Display name (for search result rendering).
        week: ISO format week start (e.g., "2026-02-10T00:00:00").
        doc_text: The canonical text from create_player_week_document().
        metadata: Additional metadata (acwr, risk_score, etc.).
    """
    global _seed_counter
    client = _get_client()
    vec = embed_text(doc_text)

    payload = {
        "player_id": player_id,
        "player_name": player_name,
        "week": week,
        "doc_type": "player_week",
        "text": doc_text,
        **metadata,
    }

    if _is_actian:
        client.upsert(COLLECTION_NAME, id=_seed_counter, vector=vec, payload=payload)
    else:
        client.upsert(doc_id=_seed_counter, vector=vec, payload=payload)

    _seed_counter += 1
    logger.info(f"Upserted player-week: {player_name} week {week}")


def search_similar_cases(query_text: str, k: int = 5,
                         source_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Searches the vector DB for similar documents and returns results in the
    format Prithvi's Flutter app expects.

    Args:
        query_text: The player-week canonical text to search against.
        k: Number of results to return.
        source_filter: Optional filter (e.g., "PitchPulse_CaseStudy").

    Returns:
        list[dict]: Each dict has:
            {
                "player_id": str,
                "player_name": str,
                "week_label": str,
                "similarity_score": float,
                "summary": str,
                "outcome": str
            }
    """
    client = _get_client()
    query_vec = embed_text(query_text)

    if _is_actian:
        raw_results = client.search(COLLECTION_NAME, query=query_vec, top_k=k)
    else:
        raw_results = client.search(query_vector=query_vec, top_k=k)

    # Format results for the Flutter app
    formatted = []
    for r in raw_results:
        payload = r.get("payload", {}) if isinstance(r, dict) else getattr(r, "payload", {})
        score = r.get("score", 0.0) if isinstance(r, dict) else getattr(r, "score", 0.0)

        # Apply source filter if specified
        if source_filter and payload.get("source") != source_filter:
            continue

        formatted.append({
            "player_id": payload.get("player_id", ""),
            "player_name": payload.get("player_name", payload.get("topic", "Historical Case")),
            "week_label": payload.get("week", payload.get("topic", "")),
            "similarity_score": round(score, 3),
            "summary": payload.get("text", "")[:200],
            "outcome": payload.get("outcome", payload.get("intervention", "")),
        })

    return formatted[:k]
