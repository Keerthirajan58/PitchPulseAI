# 🏟️ HANDOFF: Keerthi → Roshini (Final AI Integration Guide)

**Date:** Feb 21, 2026  
**Status:** ✅ All 6 AI Modules Tested & Pushed to GitHub

---

## 1. AI Modules You Need to Import

| Module | Function | Wire To |
|---|---|---|
| `backend.ai.action_plan` | `generate_action_plan(player_ctx, cases, playbook)` | `POST /players/{id}/action_plan` |
| `backend.ai.match_report` | `generate_match_report(fixture, team_stats, player_stats)` | Post-match sync worker |
| `backend.ai.movement_analysis` | `analyze_movement(video_path, position)` | `POST /players/{id}/movement_analysis` |
| `backend.ai.presage_readiness` | `process_presage_checkin(player_ctx, vitals)` | **NEW:** `POST /players/{id}/presage_checkin` |
| `backend.ai.suggested_xi` | `generate_suggested_xi(opponent, context, squad)` | **NEW:** `POST /workspaces/{id}/suggested-xi` |
| `backend.ai.vector_db` | `seed_knowledge_base()`, `upsert_player_week()`, `search_similar_cases()` | Sync worker + `GET /players/{id}/similar_cases` |
| `backend.ai.embeddings` | `embed_text()`, `create_player_week_document()` | Used internally by vector_db |

---

## 2. New Endpoints You Need to Create

### `POST /players/{id}/presage_checkin`
```python
from backend.ai.presage_readiness import process_presage_checkin

# player_ctx = fetch from DB (name, position, risk_score, readiness_score, acwr, last_match_minutes, baselines)
result = process_presage_checkin(
    player_context=player_ctx,
    vitals=request_body["vitals"]  # includes stress_level, focus, valence from Presage SDK
)
# Returns: {readiness_delta, readiness_flag, emotional_state, contributing_factors, recommendation}
```

### `POST /workspaces/{id}/suggested-xi`
```python
from backend.ai.suggested_xi import generate_suggested_xi

result = generate_suggested_xi(
    opponent="Bayern Munich",
    match_context="Away, UCL Semi-Final",
    available_squad=[  # build from workspace squad
        {"id": str(p.id), "name": p.name, "position": p.position, "readiness": metrics.readiness_score, "form": "Good"}
    ]
)
# Returns: {best_formation, tactical_analysis, starting_xi_ids, bench_ids, player_rationales}
```

---

## 3. Vector DB Key Alignment

I aligned my `search_similar_cases()` output to match YOUR `GET /players/{id}/similar_cases` contract exactly:

| Your Contract Key | My Output Key | ✅ |
|---|---|---|
| `player_name` | `player_name` | Match |
| `week_date` | `week_date` | Match |
| `similarity_score` | `similarity_score` | Match |
| `context` | `context` | Match |
| `action_taken` | `action_taken` | Match |

You can wrap my return value in `{"cases": results}` to match your response shape.

---

## 4. Vultr Deployment (for Prithvi)

Prithvi needs your API accessible from his Flutter app — not on `localhost`. Deploy to Vultr:

```bash
# On your Vultr instance:
git clone https://github.com/RoshiniVenkateswaran/PitchPulseDB.git
cd PitchPulseDB
# Create .env with GEMINI_API_KEY, SUPABASE_URL, etc.
docker-compose up -d --build
# API live at http://<vultr-ip>:8000/docs
```

Then share the Vultr IP with Prithvi so he can set it as his app's base URL.

---

## 5. Environment Variables

Ensure `.env` has:
```
GEMINI_API_KEY=your_key_here
VECTOR_DB_URL=localhost:50051    # leave blank for in-memory fallback
```

---

## 6. Full API Contract

See: **`contracts/api_contract.md`** — this is the merged, single source of truth containing ALL endpoints (yours + my AI endpoints). Share this with Prithvi.
