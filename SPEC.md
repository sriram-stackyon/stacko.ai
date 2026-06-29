# SPEC.md — Technical Specification
## AI-Forge 2026 Capstone · Project 14 · Automated Claims Adjuster

> **PRINCIPLE**: This file is the contract. If code and SPEC disagree, fix the code.

---

## 1. Folder Structure

```
project14/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app + CORS + router mounts
│   │   ├── config.py                # Settings loaded from .env
│   │   ├── models.py                # Pydantic request / response models
│   │   ├── routes/
│   │   │   └── claims.py            # POST /api/claims, GET /api/claims, GET /api/claims/{id}
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── state.py             # ClaimsState TypedDict
│   │   │   ├── pipeline.py          # StateGraph definition + compile()
│   │   │   └── nodes/
│   │   │       ├── __init__.py
│   │   │       ├── intake.py              # intake_node
│   │   │       ├── policy_verification.py # policy_verification_node
│   │   │       ├── damage_assessment.py   # damage_assessment_node
│   │   │       ├── fraud_detection.py     # fraud_detection_node
│   │   │       ├── adjudication.py        # adjudication_node
│   │   │       └── communication.py       # communication_node
│   │   └── prompts/
│   │       ├── damage_assessment_system.txt
│   │       ├── fraud_detection_system.txt
│   │       ├── adjudication_system.txt
│   │       └── communication_system.txt
│   ├── .env                         # Never committed
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── api/
│   │   │   └── claims.js            # axios wrappers
│   │   ├── components/
│   │   │   ├── ClaimForm.jsx
│   │   │   ├── ClaimResult.jsx
│   │   │   ├── EmailDraft.jsx
│   │   │   ├── ClaimsHistory.jsx
│   │   │   └── LoadingSpinner.jsx
│   │   └── pages/
│   │       ├── SubmitClaimPage.jsx
│   │       └── HistoryPage.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── docs/
│   └── architecture.mmd
├── REQUIREMENTS.md
├── SPEC.md
├── PLAN.md
├── CHECKPOINTS.md
├── DELIVERABLES.md
├── DEPENDENCIES.md
├── PROMPT_SEQUENCES.md
├── FUTURE_VISION.md
├── MVP_PREVIEW.md
└── README.md
```

---

## 2. Supabase Schema

```sql
-- Run these in the Supabase SQL Editor before writing any code.

-- 2.1 policies table (seeded with mock data)
CREATE TABLE IF NOT EXISTS policies (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  policy_number   TEXT UNIQUE NOT NULL,
  holder_name     TEXT NOT NULL,
  coverage_type   TEXT NOT NULL,     -- 'comprehensive' | 'collision' | 'third-party' | 'fire' | 'theft'
  coverage_limit  DECIMAL NOT NULL,
  deductible      DECIMAL NOT NULL,
  is_active       BOOLEAN DEFAULT true,
  expiry_date     DATE NOT NULL
);

-- Seed data
INSERT INTO policies (policy_number, holder_name, coverage_type, coverage_limit, deductible, is_active, expiry_date)
VALUES
  ('POL-001', 'Alice Johnson',   'comprehensive', 50000.00, 500.00,  true,  '2026-12-31'),
  ('POL-002', 'Bob Martinez',    'collision',     30000.00, 1000.00, true,  '2026-06-30'),
  ('POL-003', 'Carol Williams',  'third-party',   15000.00, 250.00,  true,  '2026-09-30'),
  ('POL-004', 'David Lee',       'comprehensive', 75000.00, 750.00,  false, '2024-12-31'),
  ('POL-005', 'Emily Chen',      'fire',          40000.00, 500.00,  true,  '2026-12-31');

-- 2.2 claims table
CREATE TABLE IF NOT EXISTS claims (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  policy_number           TEXT NOT NULL,
  claimant_name           TEXT NOT NULL,
  incident_type           TEXT NOT NULL,
  incident_description    TEXT NOT NULL,
  photo_urls              JSONB DEFAULT '[]',
  -- policy verification outputs
  policy_valid            BOOLEAN,
  policy_holder_name      TEXT,
  coverage_type           TEXT,
  coverage_limit          DECIMAL,
  deductible              DECIMAL,
  -- damage assessment outputs
  damage_description      TEXT,
  estimated_repair_cost   DECIMAL,
  damage_severity         TEXT,  -- 'low' | 'medium' | 'high'
  -- fraud detection outputs
  fraud_risk              TEXT,  -- 'low' | 'medium' | 'high'
  fraud_flags             JSONB DEFAULT '[]',
  -- adjudication outputs
  decision                TEXT CHECK (decision IN ('approved', 'denied', 'escalated')),
  decision_reason         TEXT,
  payout_amount           DECIMAL,
  -- communication output
  email_draft             TEXT,
  -- metadata
  created_at              TIMESTAMPTZ DEFAULT now()
);

-- 2.3 Supabase Storage bucket
-- In Supabase Dashboard > Storage > Create bucket:
--   Name: claim-photos
--   Public: true
--   Allowed MIME types: image/jpeg, image/png, image/webp
```

---

## 3. LangGraph State

### `backend/app/agents/state.py`

```python
from typing import TypedDict, Optional

class ClaimsState(TypedDict):
    # Inputs (from claim submission)
    policy_number: str
    claimant_name: str
    incident_type: str
    incident_description: str
    photo_urls: list[str]          # Public Supabase Storage URLs

    # After policy_verification_node
    policy_valid: Optional[bool]
    policy_holder_name: Optional[str]
    coverage_type: Optional[str]
    coverage_limit: Optional[float]
    deductible: Optional[float]

    # After damage_assessment_node
    damage_description: Optional[str]
    estimated_repair_cost: Optional[float]
    damage_severity: Optional[str]  # 'low' | 'medium' | 'high'

    # After fraud_detection_node
    fraud_risk: Optional[str]       # 'low' | 'medium' | 'high'
    fraud_flags: Optional[list[str]]

    # After adjudication_node
    decision: Optional[str]         # 'approved' | 'denied' | 'escalated'
    decision_reason: Optional[str]
    payout_amount: Optional[float]

    # After communication_node
    email_draft: Optional[str]

    # Error handling
    error: Optional[str]
```

---

## 4. LangGraph Pipeline

### `backend/app/agents/pipeline.py`

```
Graph topology:
  START
    → intake_node
    → policy_verification_node
    → damage_assessment_node
    → fraud_detection_node
    → adjudication_node
    → communication_node
  END

All edges are SEQUENTIAL. The adjudication_node contains the approve/deny/escalate
business logic internally — it does NOT branch the graph. The decision is stored as
a state key and the communication_node uses it for email tone.

Rationale: Branching the graph adds complexity without benefit for a 2-week demo.
The orchestrator pattern is achieved by the adjudication_node reading all upstream
outputs and making a rule-based + LLM-assisted decision.
```

---

## 5. Node Contracts

### 5.1 `intake_node(state) -> dict`
- **Input**: raw ClaimsState (policy_number, claimant_name, incident_type, incident_description, photo_urls)
- **Output**: `{}` (validation only; raises if required fields missing)
- **Side effects**: none
- **Error handling**: Returns `{"error": "Missing required field: {field}"}` if any required field is empty

### 5.2 `policy_verification_node(state) -> dict`
- **Input**: `state["policy_number"]`, `state["incident_type"]`
- **Output**: `policy_valid`, `policy_holder_name`, `coverage_type`, `coverage_limit`, `deductible`
- **Logic**: Query Supabase `policies` table where `policy_number = ?`. Check `is_active == true` and `expiry_date > today` and that `coverage_type` covers the `incident_type`.
- **Coverage mapping**:
  ```
  comprehensive → covers: collision, theft, fire, weather, vandalism
  collision     → covers: collision
  third-party   → covers: collision (other party damage)
  fire          → covers: fire
  theft         → covers: theft
  ```
- **Error handling**: `if state.get("error"): return {}`

### 5.3 `damage_assessment_node(state) -> dict`
- **Input**: `state["photo_urls"]` (1–3 public URLs), `state["incident_type"]`
- **Output**: `damage_description`, `estimated_repair_cost`, `damage_severity`
- **Logic**: Call GPT-4o with vision. Pass all photo URLs as `image_url` content parts. Use `damage_assessment_system.txt` prompt. Expect structured JSON response.
- **Error handling**: `if state.get("error"): return {}`. If no photos, set `damage_description="No photos provided"`, `estimated_repair_cost=0.0`, `damage_severity="low"`.

### 5.4 `fraud_detection_node(state) -> dict`
- **Input**: Full state (policy, damage, incident details)
- **Output**: `fraud_risk`, `fraud_flags`
- **Logic**: Query Supabase for prior claims on this `policy_number`. Pass claim history + current claim to GPT-4o with `fraud_detection_system.txt`. Expect JSON with `risk` and `flags`.
- **Fraud signals to detect**: repeated claims on same policy, estimated cost near policy limit, suspicious keywords in description, multiple claims in short period.
- **Error handling**: `if state.get("error"): return {}`

### 5.5 `adjudication_node(state) -> dict`
- **Input**: Full state (all prior node outputs)
- **Output**: `decision`, `decision_reason`, `payout_amount`
- **Logic**:
  1. If `policy_valid == False` → `decision = "denied"`, `payout_amount = None`
  2. If `fraud_risk == "high"` → `decision = "denied"`, `payout_amount = None`
  3. If `fraud_risk == "medium"` → `decision = "escalated"`, `payout_amount = None`
  4. If `estimated_repair_cost > coverage_limit` → `decision = "escalated"` (human review for large claims)
  5. Otherwise → call GPT-4o with `adjudication_system.txt` to reason over the data and produce final decision + payout
  6. Payout = `estimated_repair_cost - deductible` (if approved and > 0)
- **Error handling**: `if state.get("error"): return {}`

### 5.6 `communication_node(state) -> dict`
- **Input**: Full state (especially `decision`, `decision_reason`, `payout_amount`, `policy_holder_name`)
- **Output**: `email_draft`
- **Logic**: Call GPT-4o with `communication_system.txt`. Include decision, reason, and payout (if approved) in prompt. Tone: professional and empathetic.
- **Error handling**: `if state.get("error"): return {}`

---

## 6. FastAPI Routes

### `POST /api/claims`
- **Request**: `multipart/form-data` with fields: `policy_number`, `claimant_name`, `incident_type`, `incident_description`, and up to 3 `photo` files.
- **Process**:
  1. Upload photos to Supabase Storage → get public URLs
  2. Invoke LangGraph pipeline with initial state
  3. Save full state + decision to Supabase `claims` table
  4. Return full claim result
- **Response model**: `ClaimResultResponse`
- **Errors**: 422 for validation, 500 for pipeline failure

### `GET /api/claims`
- **Response**: `list[ClaimSummaryResponse]` — all claims, ordered by `created_at DESC`

### `GET /api/claims/{claim_id}`
- **Response**: `ClaimResultResponse` — full claim detail including email draft

---

## 7. Pydantic Models

### `backend/app/models.py`

```python
from pydantic import BaseModel, UUID4
from typing import Optional
from datetime import datetime

class ClaimSummaryResponse(BaseModel):
    id: UUID4
    policy_number: str
    claimant_name: str
    incident_type: str
    decision: Optional[str]
    payout_amount: Optional[float]
    fraud_risk: Optional[str]
    damage_severity: Optional[str]
    created_at: datetime

class ClaimResultResponse(ClaimSummaryResponse):
    incident_description: str
    photo_urls: list[str]
    policy_valid: Optional[bool]
    coverage_type: Optional[str]
    coverage_limit: Optional[float]
    damage_description: Optional[str]
    estimated_repair_cost: Optional[float]
    fraud_flags: Optional[list[str]]
    decision_reason: Optional[str]
    email_draft: Optional[str]
    error: Optional[str]
```

---

## 8. Prompts

### `damage_assessment_system.txt`
Instructs GPT-4o to:
- Analyze the provided damage photos
- Return JSON only: `{"damage_description": "...", "estimated_repair_cost": 12500.0, "damage_severity": "medium"}`
- `damage_severity` must be one of: `low`, `medium`, `high`
- Base cost estimates on realistic repair industry rates
- Never output markdown, code fences, or explanatory prose

### `fraud_detection_system.txt`
Instructs GPT-4o to:
- Analyze the claim details and prior claims history provided
- Return JSON only: `{"fraud_risk": "low", "fraud_flags": ["reason 1", "reason 2"]}`
- `fraud_risk` must be one of: `low`, `medium`, `high`
- `fraud_flags` is an empty list if no flags

### `adjudication_system.txt`
Instructs GPT-4o to:
- Review the policy status, damage estimate, and fraud risk provided
- Return JSON only: `{"decision": "approved", "decision_reason": "Policy is active. Damage is within coverage limit. Fraud risk is low.", "payout_amount": 11500.0}`
- `decision` must be one of: `approved`, `denied`, `escalated`
- `payout_amount` is null if decision is denied or escalated

### `communication_system.txt`
Instructs GPT-4o to:
- Write a professional, empathetic email to the claimant
- Return the email body as plain text (no JSON, no markdown)
- Include: salutation, brief explanation of decision, next steps (if escalated), payout amount (if approved)
- Keep to 150–250 words

---

## 9. Environment Variables

### `backend/.env.example`
```
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_STORAGE_BUCKET=claim-photos
```

---

## 10. Frontend Component Contracts

| Component | Props | Renders |
|---|---|---|
| `ClaimForm` | `onSubmit(formData): void`, `isLoading: bool` | Form with all fields + file upload (max 3 files) + submit button |
| `ClaimResult` | `claim: ClaimResultResponse` | Decision badge, damage summary card, payout amount, fraud risk indicator |
| `EmailDraft` | `emailText: string` | Pre-formatted text area (read-only) showing the generated email |
| `ClaimsHistory` | `claims: ClaimSummaryResponse[]`, `onSelect(id): void` | Sortable table with status badges |
| `LoadingSpinner` | `message: string` | Centered spinner with status message |
