# PLAN.md — Implementation Plan
## AI-Forge 2026 Capstone · Project 14 · Automated Claims Adjuster

---

## Week 1 — Backend Pipeline (Days 1–7)

### Day 1 — Scaffold + Supabase Setup
**Goal**: Empty skeleton compiles; Supabase tables + storage bucket exist.

- [ ] Create folder structure exactly as defined in SPEC.md §1
- [ ] Create `backend/requirements.txt` with all dependencies
- [ ] Create `backend/.env.example`; copy to `backend/.env` and fill values
- [ ] Create `backend/app/config.py` — loads and validates env vars
- [ ] Create `backend/app/main.py` — bare FastAPI app with CORS and health-check route
- [ ] Run Supabase schema from SPEC.md §2 in SQL Editor
- [ ] Create Supabase Storage bucket `claim-photos` (public)
- [ ] Seed `policies` table with 5 mock policies from SPEC.md §2
- [ ] Confirm backend starts: `uvicorn app.main:app --reload` from `backend/`
- [ ] Gate: `GET /health` returns `{"status": "ok"}`

### Day 2 — State + Policy Verification Node
**Goal**: Policy verification queries Supabase and returns correct verdict.

- [ ] Create `backend/app/agents/state.py` — `ClaimsState` TypedDict
- [ ] Create `backend/app/agents/nodes/policy_verification.py`
  - Query `policies` table by `policy_number`
  - Check `is_active`, `expiry_date`, coverage type vs incident type
  - Return state keys: `policy_valid`, `policy_holder_name`, `coverage_type`, `coverage_limit`, `deductible`
- [ ] Write unit test: `POL-001` + `collision` → `policy_valid: True`
- [ ] Write unit test: `POL-004` (expired) → `policy_valid: False`
- [ ] Write unit test: `POL-003` (third-party) + `fire` → `policy_valid: False` (not covered)
- [ ] Gate: All 3 unit tests pass

### Day 3 — Damage Assessment Node
**Goal**: GPT-4o vision analyzes a test photo and returns a plausible estimate.

- [ ] Create `backend/app/prompts/damage_assessment_system.txt`
- [ ] Create `backend/app/agents/nodes/damage_assessment.py`
  - Accept `photo_urls` list; pass as image_url content parts to GPT-4o
  - Parse JSON response; extract `damage_description`, `estimated_repair_cost`, `damage_severity`
  - Strip any markdown fences from LLM output before parsing JSON
- [ ] Manual test: call node with a real car damage photo URL
- [ ] Gate: Node returns non-zero `estimated_repair_cost` for a real damage photo

### Day 4 — Fraud Detection Node
**Goal**: Fraud detection correctly flags repeated claims.

- [ ] Create `backend/app/prompts/fraud_detection_system.txt`
- [ ] Create `backend/app/agents/nodes/fraud_detection.py`
  - Query `claims` table for prior claims on same `policy_number`
  - Format claim history + current claim details for GPT-4o
  - Parse JSON response: `fraud_risk`, `fraud_flags`
- [ ] Manual test: submit same policy number 3 times; third should return `fraud_risk: high`
- [ ] Gate: `fraud_risk` is one of `low`, `medium`, `high`; `fraud_flags` is a list

### Day 5 — Adjudication Node
**Goal**: Adjudication applies business rules and produces deterministic decisions for clear-cut cases.

- [ ] Create `backend/app/prompts/adjudication_system.txt`
- [ ] Create `backend/app/agents/nodes/adjudication.py`
  - Implement the 5-step business rules from SPEC.md §5.5
  - Call GPT-4o only for ambiguous cases (all business rules pass)
  - Parse JSON: `decision`, `decision_reason`, `payout_amount`
  - Calculate payout: `max(0, estimated_repair_cost - deductible)` if approved
- [ ] Unit test: expired policy → `denied`
- [ ] Unit test: `fraud_risk: high` → `denied`
- [ ] Unit test: `fraud_risk: medium` → `escalated`
- [ ] Unit test: `estimated_repair_cost > coverage_limit` → `escalated`
- [ ] Gate: All 4 unit tests pass without an LLM call

### Day 6 — Communication Node
**Goal**: Email draft is professional and references the correct decision.

- [ ] Create `backend/app/prompts/communication_system.txt`
- [ ] Create `backend/app/agents/nodes/communication.py`
  - Build a user prompt including: holder name, incident type, decision, reason, payout (if any)
  - Call GPT-4o text-only; return raw email text (no JSON parsing needed)
- [ ] Manual test: confirm email body mentions the claimant name and decision
- [ ] Gate: Email is 150–250 words; correctly references "approved" / "denied" / "escalated"

### Day 7 — Pipeline Wiring + End-to-End Node Test
**Goal**: Full LangGraph pipeline runs successfully from start to end.

- [ ] Create `backend/app/agents/pipeline.py`
  - Import all 6 node functions
  - Build `StateGraph(ClaimsState)`
  - Add nodes and sequential edges per SPEC.md §4
  - Compile once at module level: `pipeline = graph.compile()`
- [ ] Create `backend/app/agents/__init__.py` exporting `pipeline`
- [ ] Integration test: call `pipeline.invoke(initial_state)` with `POL-001`, a real photo URL, and a collision description
- [ ] Gate: Final state has non-None values for `decision`, `decision_reason`, `email_draft`

---

## Week 2 — API + Frontend + Integration (Days 8–15)

### Day 8 — FastAPI Routes
**Goal**: Both API routes exist and are testable via Swagger UI.

- [ ] Create `backend/app/models.py` — Pydantic models from SPEC.md §7
- [ ] Create `backend/app/routes/claims.py`
  - `POST /api/claims` — accepts multipart form; uploads photos to Supabase Storage; invokes pipeline; saves to `claims` table; returns `ClaimResultResponse`
  - `GET /api/claims` — returns all claims as `list[ClaimSummaryResponse]`
  - `GET /api/claims/{claim_id}` — returns single claim as `ClaimResultResponse`
- [ ] Mount router in `main.py`: `app.include_router(claims_router, prefix="/api")`
- [ ] Gate: All 3 routes appear in `/docs`; `POST /api/claims` returns 200 with a complete result

### Day 9 — Supabase Persistence
**Goal**: Claims are saved and retrievable from the database.

- [ ] Implement Supabase insert in `POST /api/claims` handler
  - Map full pipeline state to `claims` table columns
  - Return the saved claim's `id` in the response
- [ ] Implement Supabase select in `GET /api/claims` and `GET /api/claims/{claim_id}`
- [ ] Confirm photo URLs saved as JSONB array in `photo_urls` column
- [ ] Gate: Submitted claim appears in Supabase Dashboard `claims` table

### Day 10 — React Scaffold + ClaimForm
**Goal**: React app runs; ClaimForm submits successfully.

- [ ] Scaffold with `npm create vite@latest frontend -- --template react`
- [ ] Install Tailwind CSS: `npm install -D tailwindcss postcss autoprefixer && npx tailwindcss init -p`
- [ ] Install axios: `npm install axios`
- [ ] Install react-router-dom: `npm install react-router-dom`
- [ ] Create `frontend/src/api/claims.js` — axios functions: `submitClaim(formData)`, `getClaims()`, `getClaimById(id)`
- [ ] Create `ClaimForm.jsx` — all fields + multi-file upload (accept="image/*", max 3 files)
- [ ] Create `SubmitClaimPage.jsx` — renders `ClaimForm` + `LoadingSpinner` while submitting
- [ ] Proxy API calls: add `vite.config.js` proxy `"/api"` → `http://localhost:8000`
- [ ] Gate: Filling in the form and submitting sends a request to `POST /api/claims`

### Day 11 — ClaimResult Component
**Goal**: Adjudication decision renders with colour-coded badge.

- [ ] Create `ClaimResult.jsx`
  - Decision badge: green for `approved`, red for `denied`, yellow for `escalated`
  - Damage card: description, estimated cost, severity label
  - Payout section: shows payout amount or "No payout" message
  - Fraud risk pill: green/yellow/red based on `fraud_risk`
  - `decision_reason` text block
- [ ] Wire `SubmitClaimPage` to show `ClaimResult` after successful submit
- [ ] Gate: All three decision states (approved/denied/escalated) render correctly with appropriate colours

### Day 12 — EmailDraft Component
**Goal**: Generated email is readable and copyable in the UI.

- [ ] Create `EmailDraft.jsx`
  - Pre-formatted text block showing `email_draft`
  - "Copy to Clipboard" button using `navigator.clipboard.writeText()`
  - Label: "Generated Customer Email (for review — not sent automatically)"
- [ ] Add `EmailDraft` below `ClaimResult` in `SubmitClaimPage`
- [ ] Gate: Email text renders; copy button works in browser

### Day 13 — ClaimsHistory Page
**Goal**: All past claims are listed; clicking a row loads the full detail.

- [ ] Create `ClaimsHistory.jsx`
  - Table with columns: Policy #, Claimant, Incident, Decision (badge), Payout, Date
  - Click row → loads claim detail via `getClaimById(id)` → shows `ClaimResult` + `EmailDraft`
- [ ] Create `HistoryPage.jsx` — renders `ClaimsHistory`
- [ ] Add routes to `App.jsx`: `/` → `SubmitClaimPage`, `/history` → `HistoryPage`
- [ ] Add simple nav bar with links to both pages
- [ ] Gate: All submitted claims visible; clicking a row shows full detail

### Day 14 — Integration Polish
**Goal**: Loading states, error handling, and edge cases all handled.

- [ ] Add `LoadingSpinner.jsx` with descriptive message (e.g. "Analyzing damage photos...")
- [ ] Add error banner in `SubmitClaimPage` for API errors (red banner at top)
- [ ] Handle edge case: submitting expired policy (`POL-004`) → shows denied result with clear reason
- [ ] Handle edge case: submitting without photos → damage assessment gracefully returns zero cost
- [ ] Ensure Tailwind responsive layout looks clean at 1280px+ viewport
- [ ] Gate: All three demo scenarios (approved, denied, escalated) work end-to-end without console errors

### Day 15 — Demo Rehearsal
**Goal**: Evaluator can see all In-Scope features working in under 10 minutes.

- [ ] Rehearse Scenario A: `POL-001` + collision + 2 photos → **Approved** result
- [ ] Rehearse Scenario B: `POL-004` (expired) + collision → **Denied** (policy inactive)
- [ ] Rehearse Scenario C: `POL-002` + same claim submitted 3× → **Denied** (high fraud risk)
- [ ] Rehearse Scenario D: high-cost repair exceeding limit → **Escalated**
- [ ] Verify Claims History page shows all 4 scenarios
- [ ] Confirm Supabase Dashboard shows 4 rows in `claims` table
- [ ] Gate: All 4 scenarios complete in ≤ 90 seconds each; no crashes

---

## Dependency Order

```
Day 1 (Scaffold)
  → Day 2 (Policy Verification)
  → Day 3 (Damage Assessment)
  → Day 4 (Fraud Detection)
  → Day 5 (Adjudication)        ← needs Days 2, 3, 4 outputs
  → Day 6 (Communication)       ← needs Day 5 output
  → Day 7 (Pipeline wiring)     ← needs all nodes
  → Day 8 (FastAPI routes)      ← needs pipeline
  → Day 9 (Persistence)         ← needs routes
  → Day 10 (React scaffold)     ← can start parallel with Day 9
  → Day 11 (ClaimResult)        ← needs Day 10
  → Day 12 (EmailDraft)         ← needs Day 11
  → Day 13 (History)            ← needs persistence (Day 9)
  → Day 14 (Polish)
  → Day 15 (Rehearsal)
```
