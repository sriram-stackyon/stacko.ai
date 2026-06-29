# REQUIREMENTS.md — Automated Claims Adjuster
## AI-Forge 2026 Capstone · Project 14 · Insurance Tech

> **STATUS: FROZEN** — Any change to this document requires a complete revision of SPEC.md, PLAN.md, and CHECKPOINTS.md before any code changes are made.

---

## Problem Statement

Insurance companies lose billions every year to slow, manual claims processing and undetected fraud. A minor car accident claim that should take hours instead takes days because adjusters must manually verify policies, review damage photos, cross-reference historical data, and draft communications. This tool automates the entire initial adjudication pipeline: a claimant submits a claim with photos, and within seconds the system verifies their policy, assesses damage using AI vision, flags fraud signals, and either approves, denies, or escalates the claim — then generates the customer communication automatically. It eliminates the bottleneck for straightforward claims while ensuring complex cases still reach human reviewers.

---

## Development Strategy — Specification-Driven AI-First Development

This project uses **Specification-Driven Development (SDD)** — every node, schema, and route is defined in SPEC.md before any code is written. The LLM is a typed pipeline node, not the architect.

| Traditional | Specification-Driven (This Project) |
|---|---|
| Code then document | SPEC.md first; code satisfies the contract |
| Improvised prompts | Prompts stored in `backend/app/prompts/*.txt` |
| "Done-ish" | Gate criteria in CHECKPOINTS.md; a phase is only complete when every gate is green |
| Architecture emerges | Committed in `docs/architecture.mmd` before Day 1 |

---

## Recommended Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| Backend | Python 3.11+ + FastAPI + Uvicorn | Fast to build, async-friendly, excellent for AI pipelines |
| AI Orchestration | LangGraph `StateGraph` (orchestrator pattern) | Handles conditional routing (approve/deny/escalate) natively |
| LLM + Vision | OpenAI GPT-4o (text + vision in one model) | Single API for both fraud analysis AND damage photo assessment |
| Frontend | React 18 + Vite + Tailwind CSS | Minimal setup, component-driven, no CSS framework fights |
| Database | Supabase (PostgreSQL) | Free tier, REST API via `supabase-py`, stores claims + policy mock data |
| Photo Storage | Supabase Storage | Built-in file storage, returns public URLs for GPT-4o vision |
| HTTP Client | `httpx` | Async, Pydantic-friendly, replaces `requests` |

---

## In-Scope Features

1. **Claim Submission UI** — Web form where a claimant enters: policy number, incident type (collision / theft / weather / fire), incident description, and uploads 1–3 damage photos.
2. **Policy Verification Node** — Checks the submitted policy number against the `policies` table in Supabase. Confirms the policy is active and the incident type is covered. Returns: `policy_valid: bool`, `coverage_type: str`, `coverage_limit: float`.
3. **Damage Assessment Node** — Uploads photo(s) to Supabase Storage, passes public URL(s) to GPT-4o vision. Returns: `damage_description: str`, `estimated_repair_cost: float`, `severity: low|medium|high`.
4. **Fraud Detection Node** — Sends claim details + claimant's claim history (from Supabase) to GPT-4o. Returns: `fraud_risk: low|medium|high`, `fraud_flags: list[str]`.
5. **Claims Adjudication Node (Orchestrator)** — Combines outputs of nodes 2–4 with business rules and LLM reasoning to return: `decision: approved|denied|escalated`, `decision_reason: str`, `payout_amount: float | None`.
6. **Customer Communication Node** — Generates a professional email draft to the claimant explaining the decision. Displayed in UI (not actually sent in MVP).
7. **Claims Result UI** — Displays the full adjudication result: decision badge (green/red/yellow), damage summary, payout amount, fraud risk level, and the generated email draft.
8. **Claims History UI** — Lists all past claims with policy number, decision, payout amount, and timestamp. Clicking a row shows the full claim detail.
9. **Supabase Persistence** — Every claim is saved to the `claims` table with all node outputs, decisions, and generated email.

---

## Out-of-Scope Features

| Feature | Reason Deferred |
|---|---|
| Actual email / SMS sending | Requires email service integration (SendGrid/Twilio); not AI work |
| Real insurance policy API | No real insurer API available; mock Supabase table is equivalent for demo |
| ML-based fraud model (custom-trained) | Requires training data and MLOps pipeline; LLM-based detection is sufficient for demo |
| User authentication / claimant login | Adds 3+ days of scope with no AI value; all claims are anonymous for demo |
| Payment processing / disbursement | Purely financial infrastructure; outside AI scope |
| Multi-claim batch processing | Single claim at a time is sufficient for demo |
| Mobile app | Web-only for demo; mobile adds no new AI capability |
| Real-time claim status tracking (WebSockets) | Polling is sufficient for a 2-week demo |

---

## Assumptions

### Environment
- Python 3.11+ installed (tested on 3.13).
- Node.js 18+ and npm installed.
- All Python dependencies installable via `pip install -r requirements.txt`.

### Data
- A `policies` table is pre-seeded in Supabase with 5–10 mock policies covering different incident types.
- Claims history for fraud detection is drawn from a `claims` table in Supabase (empty at start; grows as demo runs).
- Damage photos are JPEG/PNG ≤ 10 MB each; GPT-4o vision handles them via public Supabase Storage URL.

### User
- The demo user is the adjuster or evaluator — not a real claimant.
- The user knows a valid policy number from the seeded data (e.g. `POL-001`).
- No identity verification is required.

### Integration
- `OPENAI_API_KEY` and optionally `OPENAI_BASE_URL` (for LiteLLM proxy) are set in `backend/.env`.
- `SUPABASE_URL` and `SUPABASE_ANON_KEY` are set in `backend/.env`.
- Supabase Storage bucket named `claim-photos` exists and is public.

### LLM
- GPT-4o is used for all 3 LLM nodes (damage assessment vision, fraud detection text, adjudication text).
- Temperature `0.1` for adjudication (deterministic decisions), `0.2` for damage and fraud nodes.
- Max tokens `1024` per node (decisions are structured JSON, not prose).

---

## Success Criteria

1. Submitting a valid policy number (`POL-001`) + incident type + description + 1 photo produces a full adjudication decision (approved/denied/escalated) within **90 seconds**.
2. The damage assessment returns a numeric `estimated_repair_cost` that is **non-zero and plausible** given the photo (verified manually during demo).
3. Submitting the same policy number 3 times in rapid succession causes the fraud detection node to return `fraud_risk: high` with at least one `fraud_flag` mentioning repeated claims.
4. Every completed claim is **visible in the Claims History tab within 5 seconds** of the decision being displayed.
5. A non-technical observer watching the demo can explain the difference between an **approved**, **denied**, and **escalated** claim within 60 seconds of seeing the results UI.

---

## Deliverables List

See [DELIVERABLES.md](./DELIVERABLES.md) for the full demo checklist.

---

## 2-Week Capacity Reality Check

### Week 1 — Backend Pipeline (Days 1–7)

| Day | Target |
|---|---|
| 1 | Repo scaffold, folder structure, `requirements.txt`, `.env.example`, Supabase tables + Storage bucket created |
| 2 | `PolicyVerificationNode` — queries Supabase `policies` table, returns coverage verdict |
| 3 | `DamageAssessmentNode` — uploads photo to Supabase Storage, calls GPT-4o vision, returns cost estimate |
| 4 | `FraudDetectionNode` — queries claim history, calls GPT-4o text, returns risk score |
| 5 | `AdjudicationNode` — orchestrator logic combining all node outputs with business rules |
| 6 | `CustomerCommunicationNode` — generates email draft from decision |
| 7 | LangGraph `StateGraph` wired end-to-end; full pipeline test with mock claim passes |

### Week 2 — API + Frontend + Integration (Days 8–15)

| Day | Target |
|---|---|
| 8 | FastAPI routes: `POST /api/claims` and `GET /api/claims` implemented |
| 9 | Supabase persistence integrated; claim saved and retrieved correctly |
| 10 | React app scaffolded; `ClaimForm` component with photo upload working |
| 11 | `ClaimResult` component shows decision badge, damage summary, payout, fraud risk |
| 12 | `EmailDraft` component shows generated customer email |
| 13 | `ClaimsHistory` page lists all past claims; clicking reloads full detail |
| 14 | End-to-end integration test; polish: loading states, error banners, responsive layout |
| 15 | Demo rehearsal: 3 scenarios (approved, denied, escalated) + fraud trigger test |

### Risk Assessment

| Risk | Likelihood | Mitigation |
|---|---|---|
| GPT-4o vision slow on large photos | Medium | Resize photos client-side to ≤ 1024px before upload |
| Supabase Storage public URL not accessible to GPT-4o | Low | Test Day 3; fallback: base64-encode the image inline |
| Adjudication logic produces wrong decisions | Medium | Write explicit business rules in the system prompt; add unit tests for edge cases |
| Photo upload CORS issues from React | Low | Configure Supabase Storage CORS policy on Day 1 |

### Verdict
**ACHIEVABLE.** The pipeline has 5 nodes but 3 of them are single LLM calls with structured JSON output. The orchestrator node is logic-only (no LLM). Photo upload via Supabase Storage is a well-documented pattern. The hardest part is the adjudication prompt — allow 1 full day for prompt tuning.
