# PROMPT_SEQUENCES.md — Master End-to-End Build Prompt
## AI-Forge 2026 Capstone · Project 14 · Automated Claims Adjuster

> This file contains the single master Copilot Agent Mode prompt to build the entire project from scratch, plus individual node prompts for targeted work.

---

## Master End-to-End Prompt

Copy this entire block into GitHub Copilot Agent Mode (Chat panel, Agent mode) to build the complete system from scratch. The prompt is self-contained and does not require any prior context.

---

```
You are building "Automated Claims Adjuster" — a full-stack AI application for Project 14 of the AI-Forge 2026 Capstone.

READ SPEC.md AND REQUIREMENTS.md COMPLETELY BEFORE WRITING ANY CODE. If they do not exist, ask me to provide them. Treat them as immutable contracts — all code must satisfy these specifications exactly.

---

## TECH STACK (MANDATORY — no substitutions)

Backend:
- Python 3.11+ with FastAPI + Uvicorn
- LangGraph StateGraph (sequential 6-node pipeline)
- OpenAI SDK (model: gpt-4o, with vision support)
- httpx for all HTTP calls (NEVER use requests)
- supabase-py for database and storage
- python-dotenv for environment variables
- pydantic v2 for all request/response models
- python-multipart for file upload handling

Frontend:
- React 18 + Vite
- Tailwind CSS (ONLY CSS framework allowed)
- axios for API calls
- react-router-dom v6

---

## FOLDER STRUCTURE

Create this exact structure:
```
backend/
  app/
    __init__.py
    main.py
    config.py
    models.py
    routes/
      __init__.py
      claims.py
    agents/
      __init__.py
      state.py
      pipeline.py
      nodes/
        __init__.py
        intake.py
        policy_verification.py
        damage_assessment.py
        fraud_detection.py
        adjudication.py
        communication.py
    prompts/
      damage_assessment_system.txt
      fraud_detection_system.txt
      adjudication_system.txt
      communication_system.txt
  .env.example
  requirements.txt
frontend/
  src/
    main.jsx
    App.jsx
    api/claims.js
    components/
      ClaimForm.jsx
      ClaimResult.jsx
      EmailDraft.jsx
      ClaimsHistory.jsx
      LoadingSpinner.jsx
    pages/
      SubmitClaimPage.jsx
      HistoryPage.jsx
  index.html
  package.json
  vite.config.js
docs/
  architecture.mmd
```

---

## PHASE 1 — BACKEND INFRASTRUCTURE

### Step 1: requirements.txt
Create backend/requirements.txt:
```
fastapi==0.115.5
uvicorn[standard]==0.32.1
python-multipart==0.0.12
langgraph==0.2.60
openai==1.57.0
httpx==0.27.2
supabase==2.10.0
python-dotenv==1.0.1
pydantic==2.10.3
```

### Step 2: config.py
Load from backend/.env using python-dotenv with Path(__file__).parent.parent / ".env" as the absolute path.
Export: OPENAI_API_KEY, OPENAI_BASE_URL (default "https://api.openai.com/v1"), LLM_MODEL (default "gpt-4o"), SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_STORAGE_BUCKET (default "claim-photos").
NEVER log or print OPENAI_API_KEY or SUPABASE_ANON_KEY.

### Step 3: main.py
- FastAPI app with CORS allowing all origins (for demo)
- Mount claims router at prefix "/api"
- GET /health returns {"status": "ok"}
- Use logging, not print()

### Step 4: Supabase Schema
Provide the exact SQL to run in Supabase SQL Editor to create:
- policies table (with seed data for POL-001 through POL-005)
- claims table (with all columns matching ClaimsState)
Also provide instructions for creating the "claim-photos" storage bucket (public).

---

## PHASE 2 — LANGGRAPH NODES

### State (state.py)
Create ClaimsState as a TypedDict with these keys:
- Inputs: policy_number, claimant_name, incident_type, incident_description, photo_urls (list[str])
- Policy outputs: policy_valid (bool|None), policy_holder_name, coverage_type, coverage_limit, deductible
- Damage outputs: damage_description, estimated_repair_cost (float|None), damage_severity
- Fraud outputs: fraud_risk, fraud_flags (list[str]|None)
- Adjudication outputs: decision, decision_reason, payout_amount (float|None)
- Communication output: email_draft
- Error: error (str|None)

### Node Rules (MANDATORY for every node):
1. Signature: (state: ClaimsState) -> dict
2. First line (except intake_node): if state.get("error"): return {}
3. Returns only a dict of state keys to update — never the full state
4. Uses logging.info() / logging.error() — never print()
5. Catches specific exceptions (never bare except:)
6. Has a one-line docstring

### intake_node (intake.py)
Validate that policy_number, claimant_name, incident_type, incident_description are all non-empty strings.
If any is missing or empty: return {"error": "Missing required field: {field_name}"}
Otherwise: return {}

### policy_verification_node (policy_verification.py)
Query Supabase policies table: SELECT * FROM policies WHERE policy_number = ?
Check: is_active == True AND expiry_date >= today
Coverage mapping (incident_type → valid coverage_types):
  collision → comprehensive, collision, third-party
  theft → comprehensive, theft
  fire → comprehensive, fire
  weather → comprehensive
  vandalism → comprehensive
If policy not found: policy_valid = False, return only policy_valid key
If found but not active/expired: policy_valid = False
If found but incident not covered: policy_valid = False
If all checks pass: policy_valid = True, also return policy_holder_name, coverage_type, coverage_limit, deductible

### damage_assessment_node (damage_assessment.py)
Load system prompt from backend/app/prompts/damage_assessment_system.txt
If photo_urls is empty: return {"damage_description": "No photos provided", "estimated_repair_cost": 0.0, "damage_severity": "low"}
Call OpenAI client (using config.OPENAI_BASE_URL and config.OPENAI_API_KEY) with model config.LLM_MODEL, temperature=0.2, max_tokens=1024
Build messages: system prompt + user message with all photo_urls as image_url content parts
Parse JSON from response (strip markdown fences if present)
Return: damage_description, estimated_repair_cost, damage_severity

### fraud_detection_node (fraud_detection.py)
Query Supabase claims table for prior claims: SELECT * FROM claims WHERE policy_number = ? ORDER BY created_at DESC LIMIT 10
Load system prompt from fraud_detection_system.txt
Build user prompt with: current claim details + prior claims history (formatted as JSON)
Call GPT-4o, temperature=0.2, max_tokens=512
Parse JSON response, strip fences
Return: fraud_risk (low/medium/high), fraud_flags (list of strings)

### adjudication_node (adjudication.py)
Apply business rules IN ORDER (no LLM call for these):
1. If policy_valid == False: return {"decision": "denied", "decision_reason": "Policy is invalid, inactive, or does not cover this incident type.", "payout_amount": None}
2. If fraud_risk == "high": return {"decision": "denied", "decision_reason": f"High fraud risk detected. Flags: {', '.join(fraud_flags)}", "payout_amount": None}
3. If fraud_risk == "medium": return {"decision": "escalated", "decision_reason": "Medium fraud risk — requires human adjuster review.", "payout_amount": None}
4. If estimated_repair_cost > coverage_limit: return {"decision": "escalated", "decision_reason": f"Claim amount (${estimated_repair_cost:,.0f}) exceeds coverage limit (${coverage_limit:,.0f}).", "payout_amount": None}
For all other cases: call GPT-4o with adjudication_system.txt, pass all state values as context, parse JSON
Calculate payout: if decision == "approved": payout_amount = max(0.0, estimated_repair_cost - deductible), else None
Return: decision, decision_reason, payout_amount

### communication_node (communication.py)
Load communication_system.txt
Build user prompt with: holder name, incident type, decision, decision_reason, payout_amount (or "no payout")
Call GPT-4o, temperature=0.3, max_tokens=512
Return raw text (NOT JSON) as email_draft — do NOT parse JSON here

### pipeline.py
Build StateGraph(ClaimsState):
  graph.add_node("intake", intake_node)
  graph.add_node("policy_verification", policy_verification_node)
  graph.add_node("damage_assessment", damage_assessment_node)
  graph.add_node("fraud_detection", fraud_detection_node)
  graph.add_node("adjudication", adjudication_node)
  graph.add_node("communication", communication_node)
  graph.add_edge(START, "intake")
  graph.add_edge("intake", "policy_verification")
  graph.add_edge("policy_verification", "damage_assessment")
  graph.add_edge("damage_assessment", "fraud_detection")
  graph.add_edge("fraud_detection", "adjudication")
  graph.add_edge("adjudication", "communication")
  graph.add_edge("communication", END)
Compile once at module level: pipeline = graph.compile()

---

## PHASE 3 — FASTAPI ROUTES

### models.py
Create ClaimSummaryResponse and ClaimResultResponse as Pydantic BaseModel classes.
ClaimSummaryResponse: id, policy_number, claimant_name, incident_type, decision, payout_amount, fraud_risk, damage_severity, created_at
ClaimResultResponse extends ClaimSummaryResponse with: incident_description, photo_urls, policy_valid, coverage_type, coverage_limit, damage_description, estimated_repair_cost, fraud_flags, decision_reason, email_draft, error

### routes/claims.py
POST /api/claims (accept multipart/form-data):
  1. Accept fields: policy_number, claimant_name, incident_type, incident_description (Form fields)
  2. Accept files: photos (UploadFile list, optional, max 3)
  3. Upload each photo to Supabase Storage bucket "claim-photos": upload bytes with content_type
  4. Collect public URLs: supabase.storage.from_("claim-photos").get_public_url(path)
  5. Build initial ClaimsState dict with all form fields and photo_urls list
  6. Invoke pipeline: final_state = pipeline.invoke(initial_state)
  7. Insert final_state into Supabase claims table
  8. Return ClaimResultResponse built from final_state + inserted row id

GET /api/claims:
  Query: SELECT * FROM claims ORDER BY created_at DESC
  Return list[ClaimSummaryResponse]

GET /api/claims/{claim_id}:
  Query: SELECT * FROM claims WHERE id = claim_id
  Return ClaimResultResponse or 404

---

## PHASE 4 — REACT FRONTEND

### Setup
- Create Vite React app in frontend/
- Install Tailwind CSS with PostCSS
- Install axios and react-router-dom
- Configure vite.config.js to proxy "/api" to "http://localhost:8000"

### App.jsx
Two routes: "/" → SubmitClaimPage, "/history" → HistoryPage
Add a simple nav bar with links to both routes

### api/claims.js
Three axios functions:
- submitClaim(formData): POST to /api/claims with FormData (multipart)
- getClaims(): GET /api/claims
- getClaimById(id): GET /api/claims/{id}

### ClaimForm.jsx
Fields:
- Policy Number (text input, required)
- Claimant Name (text input, required)
- Incident Type (select: Collision, Theft, Fire, Weather, Vandalism)
- Incident Description (textarea, required)
- Photo Upload (input type=file, accept="image/*", multiple, max 3 — validate client-side)
Submit button disabled when isLoading=true

### ClaimResult.jsx
Show:
- Decision badge: green/Approved, red/Denied, yellow/Escalated (Tailwind bg-green-100, bg-red-100, bg-yellow-100)
- Damage card: description, estimated_repair_cost formatted as currency, damage_severity
- Fraud risk pill: same color coding
- Payout section: show payout_amount formatted as currency or "No payout applicable"
- Decision reason text block (gray background, full width)

### EmailDraft.jsx
- Label: "Generated Customer Communication (preview — not sent automatically)"
- Read-only textarea or pre block showing email_draft
- "Copy Email" button using navigator.clipboard.writeText()

### ClaimsHistory.jsx
Table with columns: Policy #, Claimant, Incident Type, Decision (badge), Payout, Date
Clicking a row calls onSelect(claim.id) which triggers getClaimById and shows ClaimResult + EmailDraft in a detail panel below

### LoadingSpinner.jsx
Centered spinner with configurable message prop: default "Processing claim..."
Include step messages in SubmitClaimPage so user knows what's happening

### SubmitClaimPage.jsx
States: idle → loading (show spinner) → result (show ClaimResult + EmailDraft) → error (show red banner)

---

## PHASE 5 — SYSTEM PROMPTS

Create these prompt files. Each must instruct GPT-4o to return ONLY the specified format with no markdown fences, no explanatory text.

### backend/app/prompts/damage_assessment_system.txt
You are an automotive damage assessment specialist. You will be shown photos of vehicle or property damage.
Analyze the photos carefully and return ONLY this JSON (no markdown, no explanation):
{"damage_description": "description of visible damage", "estimated_repair_cost": 0.0, "damage_severity": "low"}
damage_severity must be exactly one of: low, medium, high
estimated_repair_cost is in USD based on realistic repair industry rates
If no damage is visible: estimated_repair_cost = 0.0, damage_severity = "low"

### backend/app/prompts/fraud_detection_system.txt
You are an insurance fraud analyst. You will receive details about a current claim and the claimant's prior claim history.
Analyze the data for fraud indicators: repeated identical claims, claim amount near policy limit, suspicious keywords, multiple claims in short period, inconsistent details.
Return ONLY this JSON (no markdown, no explanation):
{"fraud_risk": "low", "fraud_flags": []}
fraud_risk must be exactly one of: low, medium, high
fraud_flags is a list of specific reasons (empty list if no flags)
Base your assessment on facts present in the data — do not speculate beyond the evidence.

### backend/app/prompts/adjudication_system.txt
You are an experienced insurance claims adjudicator. You have already verified that the policy is valid and active, the fraud risk is low, and the claim amount is within the coverage limit. Now reason over the following claim details to make a final decision.
Return ONLY this JSON (no markdown, no explanation):
{"decision": "approved", "decision_reason": "reason", "payout_amount": 0.0}
decision must be exactly one of: approved, denied, escalated
payout_amount is the approved amount BEFORE deducting the deductible (the calling code will calculate the net payout). If denied or escalated, set payout_amount to null.
Be decisive. Most claims reaching this node should be approved unless there is a clear reason to deny.

### backend/app/prompts/communication_system.txt
You are a professional insurance claims communication specialist. Write a clear, empathetic letter to the claimant informing them of the decision on their insurance claim.
Requirements:
- Address the claimant by name
- State the decision clearly in the first paragraph
- If approved: mention the payout amount and next steps
- If denied: explain the reason and any appeals process
- If escalated: explain that a human adjuster will contact them within 3 business days
- Keep to 150-250 words
- Professional but warm tone
- No markdown formatting — plain text only
Return ONLY the email body. No subject line. No JSON.

---

## SECURITY REQUIREMENTS (NON-NEGOTIABLE)

1. OPENAI_API_KEY and SUPABASE_ANON_KEY must NEVER appear in logs, responses, or committed files
2. backend/.env must be in .gitignore
3. The frontend must NEVER import or use supabase-js — all DB access via FastAPI
4. Use Pydantic models for all FastAPI response schemas — never return raw dicts
5. httpx only — never use the requests library

---

## TESTING PROCEDURE

After completing each phase, perform these tests:

Phase 1 test: curl http://localhost:8000/health → {"status": "ok"}

Phase 2 test: Python script that calls pipeline.invoke() with:
  policy_number="POL-001", claimant_name="Test User", incident_type="collision",
  incident_description="Car was hit from behind at a red light.", photo_urls=[]
  → Expect: decision is not None, email_draft is not None

Phase 3 test: curl -X POST http://localhost:8000/api/claims with form data → expect 200 with JSON

Phase 4 test: Open http://localhost:5173, fill form, submit, verify result displays with coloured badge

Fraud test: Submit POL-002 3 times with same incident → third submission should show denied + fraud flags

---

## DONE CRITERIA

The project is complete when:
1. All 4 demo scenarios in MVP_PREVIEW.md work end-to-end without errors
2. All claims appear in the History page
3. Supabase claims table has the submitted claims
4. No API keys in any committed files
5. Backend runs from: cd backend && uvicorn app.main:app --reload
6. Frontend runs from: cd frontend && npm run dev
```

---

## Individual Node Prompts

Use these for targeted Copilot sessions when working on a specific node.

### Prompt: Policy Verification Node Only
```
Open backend/app/agents/nodes/policy_verification.py.
Implement the policy_verification_node function exactly as specified in SPEC.md §5.2.
Requirements:
- Signature: (state: ClaimsState) -> dict
- First line: if state.get("error"): return {}
- Query Supabase policies table using supabase-py client from config
- Coverage mapping: comprehensive→all, collision→collision+comprehensive+third-party, theft→theft+comprehensive, fire→fire+comprehensive, weather→comprehensive, vandalism→comprehensive
- If policy not found or not active or wrong coverage: return {"policy_valid": False}
- If all good: return all 5 output keys
- Use logging.info() not print()
- Docstring required
```

### Prompt: Damage Assessment Node Only
```
Open backend/app/agents/nodes/damage_assessment.py.
Implement damage_assessment_node using GPT-4o vision.
Requirements:
- Load system prompt from backend/app/prompts/damage_assessment_system.txt using pathlib
- If photo_urls is empty: return {"damage_description": "No photos provided", "estimated_repair_cost": 0.0, "damage_severity": "low"}
- Build OpenAI messages with system prompt + user message containing all photo_urls as image_url content parts
  Format: {"type": "image_url", "image_url": {"url": url}} for each photo
- Use temperature=0.2, max_tokens=1024
- Strip markdown fences (```json ... ```) before json.loads()
- Return: damage_description, estimated_repair_cost, damage_severity
```

### Prompt: Fix Adjudication Business Rules
```
Open backend/app/agents/nodes/adjudication.py.
The adjudication_node must apply 4 business rules BEFORE calling the LLM:
1. if not state.get("policy_valid"): return {"decision": "denied", "decision_reason": "...", "payout_amount": None}
2. if state.get("fraud_risk") == "high": return denied with fraud reason
3. if state.get("fraud_risk") == "medium": return escalated
4. if state.get("estimated_repair_cost", 0) > state.get("coverage_limit", float("inf")): return escalated

Only call GPT-4o if all 4 rules pass (ambiguous case).
After LLM decision: if approved, calculate payout_amount = max(0.0, estimated_repair_cost - deductible)
```
