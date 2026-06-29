"""Application configuration and shared clients."""

import os
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from openai import OpenAI

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ENV_PATHS = [_REPO_ROOT / ".env", _REPO_ROOT / "backend" / ".env"]

for env_path in _ENV_PATHS:
    load_dotenv(env_path, override=True, encoding="utf-8-sig")

LITELLM_PROXY_URL = os.getenv("LITELLM_PROXY_URL", "").strip()
LITELLM_VIRTUAL_KEY = os.getenv("LITELLM_VIRTUAL_KEY", "").strip()
LITELLM_MODEL = os.getenv("LITELLM_MODEL", "gpt-4o").strip()
LITELLM_USER_ID = os.getenv("LITELLM_USER_ID", "").strip()
LITELLM_DEPARTMENT = os.getenv("LITELLM_DEPARTMENT", "").strip()
LITELLM_ENVIRONMENT = os.getenv("LITELLM_ENVIRONMENT", "").strip()
LLM_MODEL = LITELLM_MODEL
DATABASE_URL = os.getenv("DATABASE_URL", "")

SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "").strip()
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "Claims Adjuster System").strip()


def get_openai_client() -> OpenAI:
    """Return an OpenAI-compatible client configured for LiteLLM."""
    if not LITELLM_PROXY_URL:
        raise ValueError("LITELLM_PROXY_URL is required.")
    if not LITELLM_VIRTUAL_KEY:
        raise ValueError("LITELLM_VIRTUAL_KEY is required.")

    default_headers: dict[str, str] = {}
    if LITELLM_USER_ID:
        default_headers["x-user-id"] = LITELLM_USER_ID
    if LITELLM_DEPARTMENT:
        default_headers["x-department"] = LITELLM_DEPARTMENT
    if LITELLM_ENVIRONMENT:
        default_headers["x-environment"] = LITELLM_ENVIRONMENT

    return OpenAI(
        api_key=LITELLM_VIRTUAL_KEY,
        base_url=LITELLM_PROXY_URL,
        default_headers=default_headers or None,
    )


def get_db_connection() -> psycopg2.extensions.connection:
    """Return a psycopg2 connection using DATABASE_URL with RealDictCursor."""
    dsn = DATABASE_URL
    if "sslmode" not in dsn:
        sep = "&" if "?" in dsn else "?"
        dsn = f"{dsn}{sep}sslmode=require"
    return psycopg2.connect(dsn, cursor_factory=psycopg2.extras.RealDictCursor)
