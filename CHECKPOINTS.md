# CHECKPOINTS.md — Quality Gates
## AI-Forge 2026 Capstone · Project 14 · Automated Claims Adjuster

> A phase is only complete when **every gate in that phase is green**. No skipping gates.

---

## Gate 1 — Infrastructure Ready
**Must pass before writing any node code.**

| # | Gate | How to Verify |
|---|---|---|
| 1.1 | `GET /health` returns `{"status": "ok"}` with HTTP 200 | `curl http://localhost:8000/health` |
| 1.2 | Supabase `policies` table exists with 5 seeded rows | Supabase Dashboard → Table Editor |
| 1.3 | Supabase `claims` table exists (empty) | Supabase Dashboard → Table Editor |
| 1.4 | Supabase Storage bucket `claim-photos` exists and is public | Supabase Dashboard → Storage |
| 1.5 | `backend/.env` has all 5 required env vars set | `python -c "from app.config import *; print('ok')"` from `backend/` |
| 1.6 | `.env` is in `.gitignore` | `git check-ignore -v backend/.env` returns a match |

**Status: ⬜ NOT STARTED**

---

## Gate 2 — LangGraph Nodes Pass Unit Tests
**Must pass before wiring the pipeline.**

| # | Gate | How to Verify |
|---|---|---|
| 2.1 | `policy_verification_node` returns `policy_valid: True` for `POL-001` + `collision` | Run unit test |
| 2.2 | `policy_verification_node` returns `policy_valid: False` for expired `POL-004` | Run unit test |
| 2.3 | `policy_verification_node` returns `policy_valid: False` for wrong incident type | Run unit test |
| 2.4 | `damage_assessment_node` returns non-zero `estimated_repair_cost` for a real damage photo URL | Manual test with live API |
| 2.5 | `damage_assessment_node` returns `estimated_repair_cost: 0.0` when `photo_urls` is empty | Run unit test |
| 2.6 | `fraud_detection_node` returns `fraud_risk: high` after 3 identical claims on same policy | Manual test sequence |
| 2.7 | `adjudication_node` returns `denied` for `policy_valid: False` without calling OpenAI | Run unit test with mock state |
| 2.8 | `adjudication_node` returns `denied` for `fraud_risk: high` without calling OpenAI | Run unit test with mock state |
| 2.9 | `adjudication_node` returns `escalated` for `fraud_risk: medium` without calling OpenAI | Run unit test with mock state |
| 2.10 | `communication_node` returns email mentioning claimant name and correct decision | Manual test with mock state |
| 2.11 | Every node returns `{}` immediately if `state.get("error")` is set | Run unit test per node |

**Status: ⬜ NOT STARTED**

---

## Gate 3 — Full Pipeline Integration
**Must pass before building the API layer.**

| # | Gate | How to Verify |
|---|---|---|
| 3.1 | `pipeline.invoke(state)` with `POL-001` + real photo → final state has non-None `decision` | Python script test |
| 3.2 | Final state `email_draft` is not empty and mentions the claimant name | Python script test |
| 3.3 | Final state `payout_amount > 0` when decision is `approved` | Python script test |
| 3.4 | `pipeline.invoke(state)` with `POL-004` (expired) → `decision: denied` within 30 seconds | Timed test |
| 3.5 | No unhandled exceptions when `photo_urls` list is empty | Python script test |

**Status: ⬜ NOT STARTED**

---

## Gate 4 — API Routes Working
**Must pass before building the frontend.**

| # | Gate | How to Verify |
|---|---|---|
| 4.1 | `POST /api/claims` with a valid form + 1 photo returns 200 with `ClaimResultResponse` JSON | Swagger UI or curl |
| 4.2 | Response includes `decision`, `decision_reason`, `email_draft`, `photo_urls` | Check response JSON |
| 4.3 | Claim is saved to Supabase `claims` table after `POST` | Supabase Dashboard |
| 4.4 | Photo is saved to Supabase Storage `claim-photos` bucket | Supabase Dashboard → Storage |
| 4.5 | `GET /api/claims` returns the saved claim in the list | `curl http://localhost:8000/api/claims` |
| 4.6 | `GET /api/claims/{id}` returns the full claim detail | Test with real claim ID |
| 4.7 | `POST /api/claims` with an invalid policy number returns 200 with `policy_valid: false` (not a 500) | Swagger UI test |

**Status: ⬜ NOT STARTED**

---

## Gate 5 — Frontend Connected to API
**Must pass before the demo rehearsal.**

| # | Gate | How to Verify |
|---|---|---|
| 5.1 | Filling and submitting the claim form triggers `POST /api/claims` (visible in browser Network tab) | Chrome DevTools |
| 5.2 | `ClaimResult` renders with coloured decision badge matching the API response | Visual inspection |
| 5.3 | Decision badge is **green** for `approved`, **red** for `denied`, **yellow** for `escalated` | Visual inspection |
| 5.4 | `EmailDraft` component shows the full email text | Visual inspection |
| 5.5 | "Copy to Clipboard" button copies email text | Test in browser |
| 5.6 | `ClaimsHistory` page lists all submitted claims with correct decision badges | Visual inspection |
| 5.7 | Clicking a history row loads that claim's full detail | Click test |
| 5.8 | Loading spinner displays while claim is being processed | Visual inspection during 30-sec wait |
| 5.9 | Error banner appears for expired policy (denied result is shown, not a crash) | Submit `POL-004` |
| 5.10 | Navigation between Submit and History pages works with browser back button | Click test |

**Status: ⬜ NOT STARTED**

---

## Gate 6 — Demo Ready
**All 4 demo scenarios rehearsed successfully.**

| # | Scenario | Expected Outcome | Status |
|---|---|---|---|
| 6.1 | `POL-001` + collision + 2 damage photos → | `approved`, payout ≈ cost − $500 deductible | ⬜ |
| 6.2 | `POL-004` (expired) + collision → | `denied`, reason: "Policy expired" | ⬜ |
| 6.3 | `POL-002` submitted 3× with same incident → | Third submission: `denied`, fraud flags present | ⬜ |
| 6.4 | `POL-001` + repair cost > $50,000 limit → | `escalated`, reason: "Claim exceeds coverage limit" | ⬜ |
| 6.5 | Claims History shows all 4 submitted claims | 4 rows with correct badges | ⬜ |
| 6.6 | Supabase Dashboard shows 4 rows in `claims` table | 4 rows with full data | ⬜ |
| 6.7 | Each scenario completes in under 90 seconds | Timed during rehearsal | ⬜ |

**Status: ⬜ NOT STARTED**
