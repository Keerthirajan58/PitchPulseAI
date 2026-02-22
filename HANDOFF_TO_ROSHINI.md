# 🏟️ HANDOFF: Keerthi → Roshini (Final AI Integration Guide)

**Date:** Feb 21, 2026  
**Status:** ✅ All 6 AI Modules Tested & Pushed to GitHub

---

## 1. AI Modules You Need to Import

| Module | Function | Wire To |
|---|---|---|
| `backend.ai.action_plan` | `generate_action_plan(player_ctx)` | `POST /players/{id}/action_plan` |
| `backend.ai.match_report` | `generate_match_report(fixture, team_stats, player_stats)` | Post-match sync worker |
| `backend.ai.movement_analysis` | `analyze_movement(video_path, position)` | `POST /players/{id}/movement_analysis` |
| `backend.ai.presage_readiness` | `process_presage_checkin(player_ctx, vitals)` | **NEW:** `POST /players/{id}/presage_checkin` |
| `backend.ai.suggested_xi` | `generate_suggested_xi(opponent, context, squad)` | **NEW:** `POST /workspaces/{id}/suggested-xi` |

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
```

---

## 6. Full API Contract

See: **`contracts/api_contract.md`** — this is the merged, single source of truth containing ALL endpoints (yours + my AI endpoints). Share this with Prithvi.
