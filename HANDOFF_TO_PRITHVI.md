# 🏟️ HANDOFF: Keerthi → Prithvi (Flutter AI Integration Guide)

**Date:** Feb 21, 2026  
**Status:** ✅ All 6 AI Modules Ready — Backend Pushed to GitHub

---

## Quick Summary

Every AI feature you need is built, tested, and documented. Your JSON models will map 1:1 with the backend responses. Below is exactly what each screen should call and what JSON it gets back.

---

## 1. Suggested XI (Your Crown Jewel 🏆)

**Your file:** `suggested_xi_screen.dart`  
**Endpoint:** `POST /workspaces/{id}/suggested-xi`

**Send:**
```json
{
  "opponent": "Bayern Munich",
  "match_context": "Away, Champions League Semi-Final",
  "available_squad": [
    {"id": "p1", "name": "Vinícius Jr", "position": "FW", "readiness": 95, "form": "Excellent"},
    {"id": "p2", "name": "Bellingham", "position": "MID", "readiness": 88, "form": "Good"}
  ]
}
```

**Receive:**
```json
{
  "best_formation": "4-3-3",
  "tactical_analysis": "4-3-3 selected to stretch Bayern's high line...",
  "starting_xi_ids": ["p1", "p2", "p3", "p4", "p5", "p6", "p7", "p8", "p9", "p10", "p11"],
  "bench_ids": ["p12", "p13", "p14", "p15"],
  "player_rationales": {
    "p1": "Vini starts — 95% readiness, excellent form, low ACWR."
  }
}
```

> Replace your hardcoded formation logic with this. `player_rationales` strings go into your `PlayerXIBottomSheet`.

---

## 2. Top Drivers (Action Plan)

**Your file:** `player_model.dart` (topDrivers)  
**Endpoint:** `POST /players/{id}/action_plan`

**Receive:**
```json
{
  "summary": "Vinicius Jr presents with elevated risk indicators.",
  "why": ["Sprint distance +25%", "Low sleep quality", "Risk score at 85"],
  "recommendations": ["Limit MD-2 drills", "Reduce HSR by 15-20%"],
  "caution": "Monitor hamstring integrity."
}
```

> The `why` array = your `topDrivers` on player cards.

---

## 3. Match Reports

**Your file:** Reports tab / `MatchReportModel`  
**Endpoint:** `GET /workspaces/{id}/reports`  (Roshini's endpoint, AI populates `headline`)

> `match_summary` from AI → maps to `headline` in report list items.

---

## 4. Presage Selfie Check-In (Camera 1)

**Where:** Check-In tab — top section  
**Endpoint:** `POST /players/{id}/presage_checkin`

**Send:**
```json
{
  "vitals": {
    "pulse_rate": 74,
    "hrv_ms": 42,
    "breathing_rate": 18,
    "stress_level": "High",
    "focus": "Low",
    "valence": "Negative",
    "confidence": 0.88
  }
}
```

**Receive:**
```json
{
  "readiness_delta": -15,
  "readiness_flag": "ALERT",
  "emotional_state": "Stressed",
  "contributing_factors": [
    "Resting HR elevated +20bpm above baseline.",
    "HRV suppressed at 52% of baseline.",
    "High psychological stress detected in facial scan."
  ],
  "recommendation": "Reduce training load and prioritize mental recovery."
}
```

**UI:** `readiness_flag` → colored badge (GREEN/AMBER/RED). `emotional_state` → secondary tag. `contributing_factors` → bullet list. `recommendation` → coaching cue card.

---

## 5. Movement Screen (Camera 2)

**Where:** Check-In tab — bottom section  
**Endpoint:** `POST /players/{id}/movement_analysis`

**Send:** Multipart form data with `video` file + `position` field.

**Receive:**
```json
{
  "mechanical_risk_band": "HIGH",
  "flags": ["Knee Valgus", "Forward Trunk Lean"],
  "coaching_cues": ["Drive knees out in line with 2nd toe.", "Cue upright chest."],
  "confidence": 0.85
}
```

---

## 6. Similar Cases

**Where:** Player Detail screen (horizontal scroll)  
**Endpoint:** `GET /players/{id}/similar_cases?k=5`

**Receive:**
```json
{
  "cases": [
    {
      "player_name": "Hazard",
      "week_date": "2023-09-15T00:00:00Z",
      "similarity_score": 0.92,
      "context": "High ACWR (1.6) combined with 3 matches in 7 days.",
      "action_taken": "Rested for 1 match, load reduced by 30%."
    }
  ]
}
```

---

## 7. Loading States (Critical for Demo!)

Every AI button needs a shimmer/loading state (Gemini takes 2-5 seconds):
- **Generate Coach Plan** → Shimmer card → JSON result drops in
- **Generate Suggested XI** → Pitch skeleton shimmer → Players appear
- **Presage Check-In** → "Analyzing vitals..." spinner → Flag overlay
- **Movement Screen** → "Analyzing biomechanics..." progress → Risk band overlay

---

## 8. Base URL

Ask Roshini for her **Vultr deployment IP**. Set your app's base URL to:
```
http://<vultr-ip>:8000
```

Interactive Swagger docs will be at `http://<vultr-ip>:8000/docs` — use this to test every endpoint from your browser before coding.

---

## 9. Action Checklist

- [ ] Wire Suggested XI → replace hardcoded formation logic
- [ ] Wire "Generate Coach Plan" → `POST /players/{id}/action_plan`
- [ ] Map `why` array → `topDrivers` on player cards
- [ ] Build **Check-In tab**: Presage Selfie (Camera 1) + Movement (Camera 2)
- [ ] Wire Similar Cases horizontal scroll → `GET /players/{id}/similar_cases`
- [ ] Map `match_summary` → `headline` in Match Report list
- [ ] Add shimmer loading states for all AI buttons
- [ ] Set base URL to Roshini's Vultr IP
