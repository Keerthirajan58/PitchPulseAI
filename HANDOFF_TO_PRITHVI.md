# 🏟️ HANDOFF: Keerthi → Prithvi (Complete AI Integration Guide)

**Date:** Feb 21, 2026  
**From:** Keerthi (AI Layer)  
**To:** Prithvi (Flutter App)  
**Status:** ✅ All 6 AI Modules Tested & Live on GitHub

---

Hey Prithvi! I reviewed your handoff — great work on the premium UI overhaul. Here's exactly how every AI feature maps to your Flutter screens, what JSON your app should send and receive, and what's already done vs. what you need to wire up.

---

## 1. What's Already Built (Your 3 LLM Touchpoints — All Handled)

### ✅ Touchpoint 1: Suggested XI Engine → `suggested_xi.py`
**Your file:** `suggested_xi_screen.dart`

**Endpoint (Roshini wires this):** `POST /api/v1/ai/suggested-xi`

**What your app sends:**
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

**What your app receives (EXACT match to your expected schema):**
```json
{
  "best_formation": "4-3-3",
  "tactical_analysis": "4-3-3 selected to stretch Bayern's high line...",
  "starting_xi_ids": ["p1", "p2", "p3", "p4", "p5", "p6", "p7", "p8", "p9", "p10", "p11"],
  "bench_ids": ["p12", "p13", "p14", "p15"],
  "player_rationales": {
    "p1": "Vini is highly recommended to start. At 95% readiness with low ACWR."
  }
}
```

**Tested & verified**: The engine correctly benches low-readiness players (e.g., Valverde at 65% and Modric at 60% were benched). It also adapts formation to opponent context. Has a deterministic fallback if Gemini is slow — your app will always get valid JSON.

---

### ✅ Touchpoint 2: Top Drivers & Action Plan → `action_plan.py`
**Your file:** `player_model.dart` (topDrivers) + Player Detail Screen

**Endpoint (Roshini wires this):** `POST /players/{id}/action_plan`

**What your app receives:**
```json
{
  "summary": "Vinicius Jr presents with elevated risk indicators.",
  "why": [
    "Sprint distance +25% vs baseline.",
    "Low sleep quality reported.",
    "Risk score at 85, readiness at 35."
  ],
  "recommendations": [
    "Limit Match Day -2 drills.",
    "Reduce high-speed running by 15-20%.",
    "Implement sleep hygiene protocols."
  ],
  "caution": "Monitor hamstring integrity daily.",
  "generated_at": "2026-02-21T10:00:00Z"
}
```

**Note:** The `why` array IS your `topDrivers`. Roshini maps the `why` values into the `top_drivers` field on the Player object for the home squad grid, and the full JSON is shown when the coach taps "Generate Coach Plan" on the Player Detail screen.

---

### ✅ Touchpoint 3: Match Reports → `match_report.py`
**Your file:** Reports tab / `MatchReportModel`

**What your app receives:**
```json
{
  "match_summary": "Real Madrid secured a 2-1 victory in a very high-intensity fixture.",
  "squad_load_assessment": "High physical toll on the squad, with elevated loads.",
  "critical_flags": ["Valverde played 90 min, ACWR approaching 1.5."]
}
```

**Note:** The `match_summary` is your "Key Takeaway" / `headline`. Roshini maps this into the report list objects.

---

## 2. NEW Features You Need to Build UI For

### 🆕 Feature A: Presage Selfie Check-In → `presage_readiness.py`
**Where it goes:** Your **Check-In tab** (new tab on bottom nav)

**UI Flow:**
1. Player opens the Check-In tab → Camera viewfinder using **Presage SmartSpectra SDK** (iOS).
2. Player takes a 10s selfie → SDK extracts vitals.
3. Your app sends the vitals to the backend.

**What your app sends:**
```json
{
  "player_id": "uuid",
  "vitals": {
    "pulse_rate": 74,
    "hrv_ms": 42,
    "breathing_rate": 18,
    "confidence": 0.88
  }
}
```

**What your app receives:**
```json
{
  "readiness_delta": -13,
  "readiness_flag": "ALERT",
  "contributing_factors": [
    "Resting HR elevated +20bpm above baseline.",
    "HRV suppressed at 52% of baseline.",
    "High ACWR combined with recent 90-min match."
  ],
  "recommendation": "Reduce training load by 20% and re-assess before match day."
}
```

**UI Display:** Show the `readiness_flag` as a colored badge (GOOD=green, CONCERN=amber, ALERT=red). Show `readiness_delta` as "+X" or "X" readiness adjustment. Show `contributing_factors` as a bullet list. Show `recommendation` as a highlighted coaching cue.

---

### 🆕 Feature B: Movement Screen → `movement_analysis.py`
**Where it goes:** Your **Check-In tab** (second section, below Selfie)

**UI Flow:**
1. Coach taps "Record Squat/Hinge" → Camera records 10s video.
2. Video uploads to backend → Gemini `gemini-2.5-pro` analyzes biomechanics.
3. Results overlay on the video thumbnail.

**What your app sends:** Multipart form upload with the video file + `player_id` + `position`.

**What your app receives:**
```json
{
  "mechanical_risk_band": "HIGH",
  "flags": ["Knee Valgus", "Forward Trunk Lean"],
  "coaching_cues": [
    "Drive knees out in line with 2nd toe on landing.",
    "Cue upright chest during deceleration practice."
  ],
  "confidence": 0.85
}
```

---

### 🆕 Feature C: Similar Historical Cases → `vector_db.py`
**Where it goes:** Player Detail screen (horizontal scroll section)

**What your app receives:**
```json
[
  {
    "player_id": "uuid",
    "player_name": "Hazard",
    "week_label": "Wk 12 (2023)",
    "similarity_score": 0.92,
    "summary": "Similar sprint spike led to hamstring overload.",
    "outcome": "Grade 1 hamstring strain in the 68th minute."
  }
]
```

---

## 3. Bottom Navigation Update

Based on our AI features, your bottom nav should be:
1. **Home** - Dashboard (Readiness Ring → Risk Alerts → Suggested XI pitch map)
2. **Check-In** - Presage Selfie + Movement Screen
3. **Reports** - Match reports list
4. **Settings** - Demo mode toggle, base URL config, logout

---

## 4. Loading States (Critical for Demo)

For every AI button, implement a **shimmer/loading** state because Gemini takes 2-5 seconds:
- "Generate Coach Plan" → Shimmer card → Drops down JSON result
- "Generate Suggested XI" → Pitch map skeleton shimmer → Players appear
- Presage Check-In → "Analyzing vitals..." spinner → Flag + delta overlay
- Movement Screen → "Analyzing movement..." progress bar → Risk band overlay

---

## 5. Quick Action Checklist

- [ ] Build the **Check-In tab** (Presage Selfie + Movement Screen).
- [ ] Wire **Suggested XI** to the new endpoint — replace hardcoded formation logic.
- [ ] Wire **"Generate Coach Plan"** button to `POST /players/{id}/action_plan`.
- [ ] Map `why` array to `topDrivers` on Player cards.
- [ ] Wire **Similar Cases** horizontal scroll to `GET /players/{id}/similar_cases`.
- [ ] Map `match_summary` to `headline` in Match Report list items.
- [ ] Add shimmer loading states for all AI-powered buttons.
- [ ] Re-order Home dashboard: **Readiness Ring** (hero) → Risk Alerts → Suggested XI.

Pull from `main` to get everything! 🚀
