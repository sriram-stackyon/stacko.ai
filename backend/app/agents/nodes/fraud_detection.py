"""Fraud detection node using prior claims history."""

import json
import logging
from pathlib import Path

from openai import OpenAIError

from app.agents.state import ClaimsState
import psycopg2
from app.config import LLM_MODEL, get_openai_client, get_db_connection


def _load_prompt() -> str:
    """Load the fraud detection system prompt from disk."""
    prompt_path = Path(__file__).resolve().parents[2] / "prompts" / "fraud_detection_system.txt"
    return prompt_path.read_text(encoding="utf-8")


def _strip_code_fences(raw: str) -> str:
    """Remove optional markdown code fences from LLM output."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    return cleaned.strip()


def _fallback_fraud_assessment(state: ClaimsState, prior_claims: list[dict]) -> dict:
    """Return deterministic fraud assessment when AI analysis is unavailable."""
    fraud_flags: list[str] = []
    risk = "low"

    recent_count = len(prior_claims)
    if recent_count >= 3:
        risk = "medium"
        fraud_flags.append("High claim frequency for this policy")

    estimated = float(state.get("estimated_repair_cost") or 0.0)
    coverage = float(state.get("coverage_limit") or 0.0)
    if coverage > 0 and estimated >= coverage * 0.9:
        risk = "medium"
        fraud_flags.append("Claim amount close to coverage limit")

    return {
        "fraud_risk": risk,
        "fraud_flags": fraud_flags,
    }


def fraud_detection_node(state: ClaimsState) -> dict:
    """Evaluate fraud risk using current claim data and recent claim history."""
    if state.get("error"):
        return {}

    policy_number = state.get("policy_number")
    prior_claims: list[dict] = []

    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM claims WHERE policy_number = %s ORDER BY created_at DESC LIMIT 10",
                    (policy_number,),
                )
                prior_claims = [dict(r) for r in cur.fetchall()]
        conn.close()
    except psycopg2.Error as exc:
        logging.warning("Fraud history lookup failed, using fallback assessment: %s", exc)

    system_prompt = _load_prompt()
    user_payload = {
        "current_claim": {
            "policy_number": state.get("policy_number"),
            "claimant_name": state.get("claimant_name"),
            "incident_type": state.get("incident_type"),
            "incident_description": state.get("incident_description"),
            "estimated_repair_cost": state.get("estimated_repair_cost"),
            "coverage_limit": state.get("coverage_limit"),
            "damage_severity": state.get("damage_severity"),
        },
        "prior_claims": prior_claims,
    }

    try:
        client = get_openai_client()
        completion = client.chat.completions.create(
            model=LLM_MODEL,
            temperature=0.2,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": "Analyze the following claim data:\n" + json.dumps(user_payload, default=str),
                },
            ],
        )
        raw = completion.choices[0].message.content or "{}"
        parsed = json.loads(_strip_code_fences(raw))

        fraud_flags = parsed.get("fraud_flags") or []
        if not isinstance(fraud_flags, list):
            fraud_flags = [str(fraud_flags)]

        risk = str(parsed.get("fraud_risk", "low")).lower()
        if risk not in {"low", "medium", "high"}:
            risk = "low"

        return {
            "fraud_risk": risk,
            "fraud_flags": [str(flag) for flag in fraud_flags],
        }
    except (OpenAIError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        logging.warning("Fraud AI analysis unavailable, using fallback assessment: %s", exc)
        return _fallback_fraud_assessment(state, prior_claims)
