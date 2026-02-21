# 🏟️ HANDOFF: Keerthi → Prithvi (UI & AI Layer Sync)

**Date:** Feb 21, 2026  
**From:** Keerthi (AI Layer)  
**To:** Prithvi (Flutter UI)  
**Status:** ✅ AI Models Ready | ⏳ Pending Flutter UI Adjustments

---

Hey Prithvi! Thanks for the update on the app side. We reviewed your progress and noticed a few critical UI structural pieces missing—specifically around the high-wow AI features. 

The good news is **your JSON data models fit the AI output perfectly**. You do *not* need to change your Pydantic/JSON models. However, we need you to adjust the App Architecture to properly showcase the AI capabilities for the 2-minute demo.

Here is the exact UI mapping and action plan you need to follow:

---

## 1. App Navigation & Structure Updates

### The Bottom Navigation Bar (4 Tabs)
Update your Bottom Nav to contain exactly these 4 tabs:
1. **Home**
2. **Check-In** *(Missing from your repo, critical for the demo)*
3. **Reports**
4. **Settings**

---

## 2. Screen-by-Screen Design Requirements

### Tab 1: Home (The Dashboard)
*Priority Change: Readiness is more actionable than Risk. The UI hierarchy must reflect this.*

1. **Next Match Card**: (Keep this as you have it—Live/Countdown).
2. **Match Readiness Score (Hero Element)**: This should be the core, most prominent metric on the dashboard. Use a large ring/donut chart showing the Squad Average Readiness (e.g., 85%).
3. **Injury Risk / Alerts (Secondary Element)**: Right below the Readiness score, show the list of the **Top 3 players flagged with HIGH risk**.
4. **Dev Tools**: Keep the "Simulate FT Update" button visible here when Demo Mode is ON.

### Tab 2: Check-In (The "High-Wow" AI Hub)
*You must build this completely new tab. This is where we show off the multimodal AI.*

1. **Section A: Selfie Check-in (Presage)**
   - UI: A camera viewfinder component with a "Take 10s Selfie" button.
   - Action: Captures vitals/readiness signals. *(Note: For the demo, you can trigger a 3-second 'Analyzing...' spinner that resolves to a mock `+5% Readiness` boost overlay if Roshini hasn't wired the endpoint).*
2. **Section B: Movement Screen**
   - UI: A "Record Squat/Hinge" button.
   - Action: This uploads a video file to Roshini's backend endpoint.
   - AI Response: Roshini's backend will call my `analyze_movement()` script and return JSON. You must overlay the `mechanical_risk_band` (LOW/MED/HIGH) and the `coaching_cues` directly over the video thumbnail once complete.

### Tab 3: Squad (Grid View) & Player Detail
Your existing Squad Grid is fine. When a coach clicks a player, they enter the **Player Detail Screen**.

*The Player Detail screen must group the AI features clearly:*
1. **Header**: Risk Trend Chart + "Why Flagged" (Drivers list).
2. **"Generate Coach Plan" Button**: 
   - When tapped, trigger `POST /players/{id}/action_plan`.
   - Show a sleek **shimmer loading state**.
   - Upon success, render a stylish dropdown or card containing the 4-part JSON response (`Summary`, `Why`, `Recommendations`, `Caution`).
3. **"Similar Historical Cases" Scroll**: 
   - A horizontal scrolling list of cases returned by my Actian VectorAI similarity search.

---

## 3. Data Contracts

Roshini and I have formalized the exact JSON structures in `contracts/api_contract.md`. **Please refer to this file in the backend repo for all final payload shapes.**

For your action items:
- The `POST /action_plan` endpoint returns the keys: `{"summary", "why": [str], "recommendations": [str], "caution", "generated_at"}`. 
- *Note the plural `recommendations` — your Flutter model expects this, and the AI layer is now configured to provide it.*

---

## 4. Next Steps for You (Prithvi)

1. **Build the `Check-In` Tab** (Selfie & Movement UI).
2. **Re-order the Home Dashboard** (Readiness > Risk).
3. **Mock the "Loading" states** for the AI generation buttons (Coach Plan, Movement Screen) so they feel premium while Gemini is thinking.
4. **Point your BASE_URL** to Roshini's deployment once she provides the Vultr IP.

Let us know when these UI shells are ready so we can run the end-to-end integration test! 🚀
