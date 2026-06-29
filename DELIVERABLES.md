# DELIVERABLES.md — Demo Checklist
## AI-Forge 2026 Capstone · Project 14 · Automated Claims Adjuster

> Mark each item `[x]` only when it works correctly end-to-end — not just when the code exists.

---

## Core Features

- [ ] **1. Claim Submission Form** — Web UI with all required fields: policy number, claimant name, incident type (dropdown), incident description, and photo upload (1–3 images, JPEG/PNG).
- [ ] **2. Policy Verification** — Submitting `POL-001` confirms the policy is active and covers the incident type. Submitting `POL-004` (expired) results in a denied claim.
- [ ] **3. Damage Assessment (Vision AI)** — At least 1 damage photo is processed by GPT-4o vision; a plausible `estimated_repair_cost` and `damage_severity` are returned and displayed.
- [ ] **4. Fraud Detection** — Submitting the same policy number 3+ times causes the third claim to receive `fraud_risk: high` with at least one `fraud_flag` in the response.
- [ ] **5. Claims Adjudication** — The system produces a clear `approved`, `denied`, or `escalated` decision with a human-readable `decision_reason`.
- [ ] **6. Payout Calculation** — An `approved` claim shows `payout_amount = estimated_repair_cost − deductible` (minimum 0).
- [ ] **7. Customer Email Draft** — A professional email addressed to the claimant is generated and displayed in the UI for all claim outcomes.
- [ ] **8. Claims History** — All submitted claims are listed in the History page with policy number, decision badge, and timestamp.
- [ ] **9. Claim Detail View** — Clicking any history row shows the full adjudication breakdown and email draft for that claim.
- [ ] **10. Supabase Persistence** — All claims are stored in the `claims` table; all photos are stored in the `claim-photos` Supabase Storage bucket.

---

## Technical Requirements

- [ ] **11. LangGraph Pipeline** — All 6 nodes (intake → policy verification → damage assessment → fraud detection → adjudication → communication) are sequential LangGraph nodes, never calling each other directly.
- [ ] **12. Error Guard on Every Node** — Each node returns `{}` immediately if `state.get("error")` is set.
- [ ] **13. Prompts as `.txt` Files** — All 4 LLM system prompts are stored in `backend/app/prompts/` — no hardcoded prompt strings in `.py` files.
- [ ] **14. Pydantic Response Models** — `POST /api/claims` and `GET /api/claims` return validated `ClaimResultResponse` / `ClaimSummaryResponse` objects.
- [ ] **15. No `requests` Library** — All HTTP calls use `httpx`; confirmed by searching for `import requests` in backend code.

---

## Security Requirements

- [ ] **16. Secrets Not Committed** — `backend/.env` is in `.gitignore`; no API keys appear in any committed file.
- [ ] **17. URL Validation** — No user-controlled URLs reach OpenAI; photo uploads are to Supabase Storage (server-controlled), not to arbitrary URLs.
- [ ] **18. Frontend Never Calls Supabase** — All database reads/writes go through FastAPI routes; no `supabase-js` client in frontend.

---

## Demo Scenarios

- [ ] **19. Scenario A — Approved Claim**: `POL-001` + `collision` + 2 damage photos → `approved` with payout > $0.
- [ ] **20. Scenario B — Denied (Expired Policy)**: `POL-004` + any incident → `denied`, reason clearly states policy is expired or inactive.
- [ ] **21. Scenario C — Denied (High Fraud Risk)**: `POL-002` submitted 3× with same incident → third submission returns `denied` with fraud flags.
- [ ] **22. Scenario D — Escalated (Over Coverage Limit)**: Any policy + damage exceeding coverage limit → `escalated` for human review.
- [ ] **23. Live Rehearsal** — All 4 scenarios demonstrated to evaluator without crashes, in under 10 minutes total.

---

## Summary Table

| Area | Items | Complete |
|---|---|---|
| Core Features | 1–10 | 0/10 |
| Technical Requirements | 11–15 | 0/5 |
| Security | 16–18 | 0/3 |
| Demo Scenarios | 19–23 | 0/5 |
| **Total** | **23** | **0/23** |
