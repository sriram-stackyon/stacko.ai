# Automated Claims Adjuster
## AI-Forge 2026 Capstone · Project 14 · Insurance Tech

An end-to-end AI pipeline that processes insurance claims in under 90 seconds — verifying policies, assessing damage from photos using GPT-4o vision, detecting fraud, adjudicating claims (approved / denied / escalated), and generating customer communications automatically.

---

## Features

| Feature | Status |
|---|---|
| Claim submission form (policy, incident, photos) | ⬜ Pending |
| Policy verification (Supabase mock policies) | ⬜ Pending |
| Damage assessment via GPT-4o vision | ⬜ Pending |
| Fraud detection via LLM pattern analysis | ⬜ Pending |
| Claims adjudication (approved/denied/escalated) | ⬜ Pending |
| Customer email draft generation | ⬜ Pending |
| Claims history with detail view | ⬜ Pending |
| Supabase persistence (claims + photos) | ⬜ Pending |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+ · FastAPI · Uvicorn |
| AI Orchestration | LangGraph StateGraph (6-node sequential pipeline) |
| LLM + Vision | OpenAI GPT-4o |
| Frontend | React 18 · Vite · Tailwind CSS |
| Database | Supabase (PostgreSQL) |
| Photo Storage | Supabase Storage |
| HTTP Client | httpx |

---

## Pipeline Architecture

```
Claim Submission
      ↓
  intake_node              ← validates required fields
      ↓
  policy_verification_node ← queries Supabase policies table
      ↓
  damage_assessment_node   ← GPT-4o vision analyzes damage photos
      ↓
  fraud_detection_node     ← LLM checks claim history for fraud signals
      ↓
  adjudication_node        ← business rules + LLM → approved/denied/escalated
      ↓
  communication_node       ← generates customer email draft
      ↓
  Claim Result (UI + DB)
```

---

## Project Structure

```
project14/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app
│   │   ├── config.py          # Environment config
│   │   ├── models.py          # Pydantic schemas
│   │   ├── routes/claims.py   # API routes
│   │   ├── agents/
│   │   │   ├── state.py       # ClaimsState TypedDict
│   │   │   ├── pipeline.py    # LangGraph StateGraph
│   │   │   └── nodes/         # 6 pipeline nodes
│   │   └── prompts/           # LLM system prompts (.txt)
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/claims.js      # axios wrappers
│       ├── components/        # ClaimForm, ClaimResult, etc.
│       └── pages/             # SubmitClaim, History
├── docs/architecture.mmd
└── [planning documents]
```

---

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Supabase account (free tier)
- OpenAI API key (GPT-4o access required for vision)

### 1. Clone and configure

```bash
git clone <repo-url>
cd project14
```

### 2. Backend setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys
```

### 3. Supabase setup

Run the SQL from [SPEC.md](./SPEC.md) §2 in your Supabase SQL Editor.
Create a public Storage bucket named `claim-photos`.

### 4. Start the backend

```bash
# From the backend/ directory
uvicorn app.main:app --reload
```

Backend runs at: http://localhost:8000
API docs at: http://localhost:8000/docs

### 5. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:5173

---

## Environment Variables

Create `backend/.env` based on `backend/.env.example`:

```
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_STORAGE_BUCKET=claim-photos
```

> **Never commit `.env`** — it's listed in `.gitignore`.

---

## Demo Scenarios

| Scenario | Policy | Expected Decision |
|---|---|---|
| Standard claim with photos | POL-001 (Alice, comprehensive) | Approved |
| Expired policy | POL-004 (David, expired 2024) | Denied |
| Repeated fraud attempt (3× same claim) | POL-002 (Bob) | Denied (3rd submission) |
| Claim exceeds coverage limit | Any | Escalated |

See [MVP_PREVIEW.md](./MVP_PREVIEW.md) for the full demo script.

---

## Planning Documents

| Document | Purpose |
|---|---|
| [REQUIREMENTS.md](./REQUIREMENTS.md) | Frozen scope, tech stack, assumptions, success criteria |
| [SPEC.md](./SPEC.md) | Folder structure, schema, node contracts, API routes |
| [PLAN.md](./PLAN.md) | 15-day implementation plan with daily tasks |
| [CHECKPOINTS.md](./CHECKPOINTS.md) | Quality gates for each phase |
| [DELIVERABLES.md](./DELIVERABLES.md) | Demo checklist (23 items) |
| [DEPENDENCIES.md](./DEPENDENCIES.md) | Package versions and service setup |
| [PROMPT_SEQUENCES.md](./PROMPT_SEQUENCES.md) | Master end-to-end Copilot prompt + node-specific prompts |
| [MVP_PREVIEW.md](./MVP_PREVIEW.md) | Demo script and talking points |
| [FUTURE_VISION.md](./FUTURE_VISION.md) | Post-capstone product roadmap |

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/api/claims` | Submit a new claim (multipart/form-data) |
| GET | `/api/claims` | List all claims |
| GET | `/api/claims/{id}` | Get claim detail |

---

## Security Notes

- All database access goes through the FastAPI backend — the React frontend never calls Supabase directly
- Photos are uploaded server-side to Supabase Storage; the frontend only sends files to FastAPI
- No API keys are committed to the repository
- All request inputs validated by Pydantic v2 models
