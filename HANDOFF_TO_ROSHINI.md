# 🏟️ HANDOFF: Keerthi → Roshini (AI Layer Integration Guide)

**Date:** Feb 21, 2025  
**From:** Keerthi (AI Layer)  
**To:** Roshini (Backend / FastAPI)  
**Status:** ✅ AI Layer Complete & Tested

---

## 1. What's Ready

All AI modules are implemented, tested with **live Gemini API calls**, and committed to git.

### Files You'll Import

| File | What It Does |
|---|---|
| `backend/ai/gemini_client.py` | Core Gemini wrapper (retries, strict JSON, low temp) |
| `backend/ai/embeddings.py` | `embed_text()` + canonical `PlayerWeekDoc` builder |
| `backend/ai/rag.py` | Fuses player context + VectorDB results into prompt context |
| `backend/ai/action_plan.py` | `generate_action_plan()` → strict JSON |
| `backend/ai/match_report.py` | `generate_match_report()` → strict JSON |
| `backend/ai/movement_analysis.py` | `analyze_movement(video_path)` → strict JSON |
| `backend/ai/suggested_xi.py` | `generate_suggested_xi()` → Tactical line-up & formation |
| `backend/ai/presage_readiness.py` | `process_presage_checkin()` → Vitals fusion logic |
| `backend/prompts/*` | All prompt templates (system + user) |

---

## 2. How To Call Each Function

### Action Plan (for `POST /players/{player_id}/action_plan`)
```python
from backend.ai.action_plan import generate_action_plan

result = generate_action_plan(
    player_context={
        "name": "Vinicius Jr",
        "position": "Winger",
        "metrics_this_week": {
            "risk_score": 85,
            "readiness_score": 35,
            "drivers": ["Sprint distance +25% vs baseline"]
        },
        "last_match": {"minutes": 95, "high_speed_running_m": 1200}
    },
    retrieved_cases=[  # ← from your Actian VectorAI query
        {
            "context_data": {"risk_score": 82, "drivers": ["Sprint distance +20%"]},
            "outcome": "Player suffered Grade 1 hamstring strain next match."
        }
    ],
    retrieved_playbook=[  # ← from your seeded knowledge base
        "Winger Protocol: If Sprint Distance exceeds baseline by 20%+, limit MD-2 drills."
    ]
)
# result is a dict matching your ActionPlanResponse Pydantic model
```

**Output keys:** `summary`, `why`, `recommendations`, `caution`  
*(Updated to match your plural `recommendations` key ✅)*

---

### Match Report (for post-match sync worker)
```python
from backend.ai.match_report import generate_match_report

result = generate_match_report(
    fixture_context={"opponent": "Barcelona", "result": "2-1", "intensity_rating": "Very High"},
    team_stats={"total_distance_km": 115, "avg_possession": "45%"},
    player_stats=[
        {"name": "Valverde", "minutes": 90, "load_flag": "High (ACWR approaching 1.5)"},
        {"name": "Modric", "minutes": 65, "load_flag": "Normal"}
    ]
)
```

**Output keys:** `match_summary`, `squad_load_assessment`, `critical_flags`

---

### Embeddings (for Actian VectorAI upsert)
```python
from backend.ai.embeddings import embed_text, create_player_week_document

# Step 1: Build the canonical text doc
doc_text = create_player_week_document(
    player_name="Jude Bellingham",
    week_start="2023-10-23",  # ISO format
    risk_score=72.5,
    readiness=45.0,
    acwr=1.65,
    monotony=2.1,
    strain=3.4,
    last_match_minutes=90,
    drivers=["High ACWR spike", "3 consecutive 90min matches"],
    recommended_action="Cap training minutes, monitor hamstring."
)

# Step 2: Get 3072-dim vector
vector = embed_text(doc_text)

# Step 3: Upsert to Actian VectorAI with your metadata
# metadata = {"player_id": str(player.id), "week": "2023-10-23T00:00:00", "acwr": 1.65}
```

**Vector dimension:** `3072` (from `gemini-embedding-001`)

---

### Movement Analysis (optional, for `analyze_movement`)
```python
from backend.ai.movement_analysis import analyze_movement

result = analyze_movement(video_path="/path/to/temp_uploads/clip.mp4")
```

**Output keys:** `mechanical_risk_band`, `flags`, `coaching_cues`, `confidence`  
*Falls back to `{"mechanical_risk_band": "MED", "confidence": 0.0}` if video processing fails.*

---

### Suggested XI (for `POST /workspaces/{id}/suggested-xi`)
```python
from backend.ai.suggested_xi import generate_suggested_xi

result = generate_suggested_xi(
    opponent="Bayern Munich",
    match_context="Away, UCL Semi-Final",
    available_squad=[
        {"id": "p1", "name": "Vini Jr", "position": "FW", "readiness": 95, "form": "Excellent"}
    ]
)
```
**Output keys:** `best_formation`, `tactical_analysis`, `starting_xi_ids`, `bench_ids`, `player_rationales`

---

### Presage Vitals (for `POST /players/{id}/presage_checkin`)
```python
from backend.ai.presage_readiness import process_presage_checkin

result = process_presage_checkin(
    player_context={
        "name": "Jude Bellingham", 
        "risk_score": 72, 
        "baselines": {"resting_pulse_rate": 58, "hrv_ms": 72}
    },
    vitals={
        "pulse_rate": 78, "hrv_ms": 38, "breathing_rate": 19,
        "stress_level": "High", "focus": "Low", "valence": "Negative", "confidence": 0.88
    }
)
```
**Output keys:** `readiness_delta`, `readiness_flag`, `emotional_state`, `contributing_factors`, `recommendation`


---

## 3. Changes Made Based On Your Feedback

| Your Request | What I Changed |
|---|---|
| `recommendations` (plural) | ✅ Updated prompt + schema to use `recommendations` |
| Vector metadata: `player_id`, `week`, `acwr` | ✅ My `create_player_week_document` includes all these fields in the text. You handle the metadata dict on upsert. |
| Video path from `temp_uploads/` | ✅ My `analyze_movement()` accepts a local path. You pass it after saving the upload. |

---

## 4. Dependencies

Add this to your `requirements.txt` if not already present:
```
google-generativeai
python-dotenv
```

And ensure `.env` has:
```
GEMINI_API_KEY=your_key_here
```

---

## 5. Git Setup

The repo is initialized at `/Users/keerthirajan/Desktop/PitchPulseAI`. You can:
- **Option A (same machine):** Copy/merge the `backend/ai/` and `backend/prompts/` folders into your repo.
- **Option B (remote):** We push to a shared GitHub repo and you pull.

```bash
# If setting up a shared remote:
git remote add origin https://github.com/YOUR_ORG/PitchPulseAI.git
git push -u origin main
```

---

## 6. What I'm Waiting On From You

| Item | Why I Need It |
|---|---|
| Your sync worker calling `generate_match_report()` after FT | So the demo flow works end-to-end |
| Your VectorDB query results passed into `generate_action_plan()` | So RAG actually retrieves real similar cases |
| `POST /players/{player_id}/action_plan` endpoint wired up | So the Flutter app can call it |

Once these are wired, the AI layer is fully live. Let's ship it! 🚀
