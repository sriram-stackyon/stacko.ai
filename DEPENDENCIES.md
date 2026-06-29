# DEPENDENCIES.md — Package & Service Dependencies
## AI-Forge 2026 Capstone · Project 14 · Automated Claims Adjuster

---

## Backend Python Dependencies

### `backend/requirements.txt`

```
fastapi==0.115.5
uvicorn[standard]==0.32.1
python-multipart==0.0.12      # required for multipart/form-data file uploads
langgraph==0.2.60
openai==1.57.0
httpx==0.27.2                  # pinned: supabase-py requires httpx < 0.28
supabase==2.10.0
python-dotenv==1.0.1
pydantic==2.10.3
pyyaml==6.0.2
```

### Version Constraints

| Package | Constraint | Reason |
|---|---|---|
| `httpx` | `==0.27.2` | `supabase-py` 2.x is not compatible with `httpx >= 0.28` |
| `openai` | `>=1.40.0` | Vision support via `image_url` content type requires v1.x |
| `langgraph` | `>=0.2.0` | `StateGraph` API stabilised in 0.2 |
| `python-multipart` | any | Required by FastAPI for file upload handling |

---

## Frontend Node Dependencies

### `frontend/package.json` devDependencies

```json
{
  "devDependencies": {
    "vite": "^5.4.0",
    "@vitejs/plugin-react": "^4.3.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0"
  }
}
```

### `frontend/package.json` dependencies

```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.27.0",
    "axios": "^1.7.0"
  }
}
```

---

## External Services

### OpenAI API
- **Model used**: `gpt-4o`
- **Capabilities used**: text generation + vision (image_url content parts)
- **API key**: `OPENAI_API_KEY` env var
- **Optional proxy**: Set `OPENAI_BASE_URL` to use LiteLLM or other proxy
- **Billing**: Vision API is priced per token + per image. Each damage photo costs ~$0.002–$0.01 USD depending on resolution.

### Supabase
- **Services used**:
  - PostgreSQL (tables: `policies`, `claims`)
  - Supabase Storage (bucket: `claim-photos`)
- **Auth**: `SUPABASE_ANON_KEY` (anon key is sufficient for server-side inserts)
- **Note**: Never use the `service_role` key in code — use `anon` key only

---

## Development Tools (not in requirements.txt)

| Tool | Purpose | Install |
|---|---|---|
| Black | Python formatter | `pip install black` (or use system install) |
| Ruff | Python linter | `pip install ruff` |
| Prettier | JS/JSX formatter | `npx prettier` (no install needed) |

---

## Installation Commands

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

---

## `.gitignore` Requirements

The following must be in `.gitignore` before the first commit:

```
# Environment secrets
backend/.env
.env

# Python
__pycache__/
*.pyc
.venv/
*.egg-info/

# Node
frontend/node_modules/
frontend/dist/

# OS
.DS_Store
Thumbs.db
```

**Security check**: Verify `.env` is ignored before `git init` — never commit API keys or Supabase credentials.
