# MVP_PREVIEW.md — Demo Script & Talking Points
## AI-Forge 2026 Capstone · Project 14 · Automated Claims Adjuster

> This document is for the presenter. It describes exactly what to say and click during the 10-minute demo.

---

## Setup (Before Evaluator Arrives)

1. Start the backend: open terminal in `backend/` → `uvicorn app.main:app --reload`
2. Start the frontend: open terminal in `frontend/` → `npm run dev`
3. Open browser at `http://localhost:5173`
4. Open a second tab at `http://localhost:8000/docs` (Swagger — for backup)
5. Have the Supabase Dashboard open in a third tab (shows live DB writes during demo)

---

## Opening Statement (30 seconds)

> "This is the Automated Claims Adjuster. When a customer files an insurance claim, a human adjuster normally has to manually check the policy, review damage photos, look for fraud signals, and write a decision letter — that takes hours or days. This system does all of that in under 90 seconds using a multi-node AI pipeline. Let me show you four scenarios."

---

## Scenario A — Approved Claim (2 minutes)

**What to say**: "Let's start with a straightforward claim. Alice Johnson has policy POL-001, which is active and comprehensive."

**Steps**:
1. Fill in form: Policy Number = `POL-001`, Claimant Name = `Alice Johnson`, Incident Type = `Collision`, Description = `My car was rear-ended at a traffic light. Significant damage to the rear bumper and trunk.`
2. Upload 2 damage photos (pre-downloaded to desktop)
3. Click **Submit Claim**
4. Point to the loading spinner: "The pipeline is running — policy check, damage photo analysis with GPT-4o vision, fraud scan, then the adjudication decision."
5. When result appears, point to: the green **Approved** badge, the damage description, the estimated repair cost, and the payout amount.
6. Scroll down: "And here's the automatically generated customer email, ready to send."

**Talking point**: "Notice the payout is the repair cost minus the $500 deductible — that's the business rule applied automatically."

---

## Scenario B — Denied (Expired Policy) (1.5 minutes)

**What to say**: "Now, David Lee has policy POL-004, but it expired in 2024."

**Steps**:
1. Fill in form: Policy Number = `POL-004`, Claimant Name = `David Lee`, Incident Type = `Collision`, Description = `Minor fender bender in a parking lot.`
2. No photos (test no-photo path)
3. Click **Submit Claim**
4. Point to red **Denied** badge and the reason: "Policy is inactive or expired."

**Talking point**: "The policy verification node caught this immediately — the claim never reached the damage or fraud nodes, which is why this decision is almost instant."

---

## Scenario C — Denied (Fraud Detection) (2 minutes)

**What to say**: "Now let's see the fraud detection in action. Bob Martinez has policy POL-002, but he's going to file the exact same claim three times in a row."

**Steps**:
1. Submit Claim 1: `POL-002`, Bob Martinez, Collision, `Car hit a pothole and damaged the front axle.` → note result (probably low fraud risk)
2. Submit Claim 2: Same fields → note `fraud_risk: medium` appearing
3. Submit Claim 3: Same fields → point to **Denied** badge and fraud flags

**Talking point**: "The fraud detection node queries the full claim history for this policy, then asks GPT-4o to reason about the pattern. Three identical claims in minutes is a clear red flag."

---

## Scenario D — Escalated (Over Coverage Limit) (1.5 minutes)

**What to say**: "Last scenario: Carol Williams files a claim for a total vehicle loss — $18,000 in damage, but her policy only covers $15,000."

**Steps**:
1. Submit: `POL-003`, Carol Williams, Collision, `Vehicle was totalled after a highway accident. Complete structural damage — vehicle is a write-off.`, 1 severe damage photo
2. Point to yellow **Escalated** badge
3. Point to reason: "Claim value exceeds coverage limit — requires human review."

**Talking point**: "The adjudication node has a hard business rule: claims exceeding the coverage limit always go to a human adjuster. The AI doesn't guess on high-value edge cases."

---

## History Page Demonstration (30 seconds)

Click the **History** tab in the navigation.

> "Here's every claim we just processed — all four, with their status badges and timestamps. Click any row..."

Click Scenario A: "...and you get the full adjudication breakdown, including the email draft."

---

## Supabase Live Data (30 seconds, optional)

Switch to Supabase Dashboard tab → Table Editor → `claims` table.

> "All four claims are persisted in Supabase. The damage photos are in the Storage bucket. Nothing is lost if the server restarts."

---

## Closing Statement (30 seconds)

> "To summarise: this system replaced a multi-hour manual process with a 90-second AI pipeline. Policy verification, computer vision damage assessment, fraud detection, adjudication, and customer communication — all automated, with a full audit trail in the database. The human adjuster only touches the cases that genuinely need them."

---

## Anticipated Questions

| Question | Answer |
|---|---|
| Why does it use GPT-4o instead of a dedicated insurance model? | GPT-4o supports both text and vision in a single API call, eliminating the need for a separate CV pipeline. For a 2-week project, this is the right tool. A production system would add a fine-tuned or specialized model in Phase 3. |
| How does fraud detection work without training data? | The LLM reasons about claim patterns (frequency, amount, description similarity) using its general knowledge. A real system would combine this with a trained ML model on historical labeled fraud data (see FUTURE_VISION.md). |
| Is the email actually sent? | No — the MVP displays the email draft for adjuster review. Actual sending via SendGrid/Twilio is in Phase 2. |
| What happens if GPT-4o is slow or down? | Each node has a try/except that sets `state["error"]` and short-circuits the remaining nodes. The API returns a 500 with a clear error message. |
| How is this secure? | API keys are in `.env` (never committed). The frontend never touches Supabase directly. All user inputs are validated by Pydantic. Photos are stored in Supabase Storage (server-controlled URLs). |
