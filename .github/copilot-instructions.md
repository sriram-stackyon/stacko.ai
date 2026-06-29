# GitHub Copilot Instructions — Automated Claims Adjuster
## AI-Forge 2026 Capstone · Project 14

These rules apply to every file in this repository. Copilot must follow them unconditionally.

---

## Tech Stack Rules

### Backend — Allowed
- Python 3.11+
- FastAPI + Uvicorn
- LangGraph (`StateGraph`)
- `openai` SDK (model `gpt-4o` only, with vision capability)
- `httpx` for all HTTP requests
- `supabase-py` for database access and file storage
- `python-dotenv` for environment variables
- `python-multipart` for file upload handling
- `pydantic` v2 for request/response models

### Backend — Forbidden
- `requests` library (use `httpx` instead)
- `langchain` agents or chains (use `langgraph` directly)
- Any LLM provider other than OpenAI
- Any model other than `gpt-4o`
- Direct database access via `psycopg2` or SQLAlchemy (use `supabase-py` only)
- Hardcoded secrets, API keys, or URLs
- `supabase-js` or any JavaScript Supabase client in backend code

### Frontend — Allowed
- React 18
- Vite (bundler)
- Tailwind CSS (styling)
- `axios` (HTTP client)
- `react-router-dom` v6 (routing)

### Frontend — Forbidden
- Any CSS framework other than Tailwind (no Bootstrap, MUI, Chakra)
- Any state management library (no Redux, Zustand, MobX) — React `useState`/`useEffect` only
- Direct calls to Supabase from the frontend (all DB access via FastAPI backend)
- Any component library (no shadcn, Headless UI, etc.) — build from scratch with Tailwind
- `supabase-js` — never import this in the frontend

---

## Folder Rules

- All Python backend code lives under `backend/app/`. Never place Python files at the repo root or in `frontend/`.
- All React frontend code lives under `frontend/src/`. Never place JSX/JS files in `backend/`.
- All LLM system prompts are stored as `.txt` files in `backend/app/prompts/`. Never hardcode prompt strings inside `.py` files.
- Planning documents (REQUIREMENTS.md, SPEC.md, etc.) live at the repository root.
- The architecture diagram lives in `docs/architecture.mmd`.

---

## LangGraph Agent Rules

- Every LangGraph node is a **pure function** with signature `(state: ClaimsState) -> dict`.
- Nodes return only a **dict of state keys to update** — they never return the full state.
- Nodes **never call each other directly**. All node-to-node data flow goes through the graph edges defined in `pipeline.py`.
- Edges are defined **only** in `backend/app/agents/pipeline.py`. No node file imports another node file.
- Every node must check `if state.get("error"): return {}` as its first line (except `intake_node`, which is the error-originating node).
- The `StateGraph` is compiled once at module load time in `pipeline.py` and reused for all requests.
- The pipeline is **sequential**: intake → policy_verification → damage_assessment → fraud_detection → adjudication → communication.

---

## Prompt Engineering Rules

- System prompts are stored in `backend/app/prompts/{node_name}_system.txt`.
- All LLM prompts except `communication_system.txt` must instruct the LLM to output **only valid JSON** with no markdown fences and no explanatory text.
- `communication_system.txt` instructs the LLM to output **plain text email body only** — no JSON.
- Every node that parses JSON must strip markdown code fences before calling `json.loads()`.
- Temperature is `0.2` for damage assessment and fraud detection nodes. `0.1` for adjudication. `0.3` for communication.
- Max output tokens per node is `1024`. Never exceed this.

---

## Adjudication Business Rules

These 4 business rules must be checked BEFORE any LLM call in `adjudication_node`. They are deterministic and must not be replaced by LLM reasoning:

1. `policy_valid == False` → **denied**
2. `fraud_risk == "high"` → **denied**
3. `fraud_risk == "medium"` → **escalated**
4. `estimated_repair_cost > coverage_limit` → **escalated**

Only if all 4 rules pass does the node call GPT-4o for reasoning.

---

## Security Rules

1. **Never log `OPENAI_API_KEY`** — not in debug logs, error messages, or print statements.
2. **Never expose `SUPABASE_ANON_KEY`** in frontend code, HTTP responses, or log output.
3. **The frontend must never call Supabase directly** — all database reads/writes go through FastAPI routes.
4. **The `.env` file must never be committed** — verify `.gitignore` contains `.env` before first commit.
5. **Photos are uploaded server-side** — the frontend sends files to FastAPI; FastAPI uploads to Supabase Storage. The frontend never calls Supabase Storage directly.
6. **Validate all inputs** — use Pydantic models for all FastAPI request and response schemas.

---

## Code Quality Rules

- All Python functions have a docstring (one line minimum).
- No bare `except:` clauses — always catch specific exception types.
- No `print()` statements in production code — use `logging.info()` / `logging.warning()` / `logging.error()`.
- All FastAPI route handlers use Pydantic response models (not raw `dict`).
- React components receive data via props — no global mutable state outside React state hooks.

---

## Golden Rule

> **If a feature is not listed in REQUIREMENTS.md In-Scope Features, do not build it.**

When in doubt about whether to add something, open REQUIREMENTS.md first. If the feature is in Out-of-Scope, do not implement it. If it is not mentioned at all, treat it as out-of-scope.
