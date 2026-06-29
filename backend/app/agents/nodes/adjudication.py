"""Claims adjudication node with deterministic guardrails."""

import json
import logging
from pathlib import Path

from openai import OpenAIError

from app.agents.state import ClaimsState
from app.config import LLM_MODEL, get_openai_client


def _load_prompt() -> str:
    """Load the adjudication system prompt from disk."""
    prompt_path = Path(__file__).resolve().parents[2] / "prompts" / "adjudication_system.txt"
    return prompt_path.read_text(encoding="utf-8")


def _strip_code_fences(raw: str) -> str:
    """Remove optional markdown code fences from LLM output."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    return cleaned.strip()


def adjudication_node(state: ClaimsState) -> dict:
    """Apply business rules and generate final adjudication decision."""
    if state.get("error"):
        return {}

    if state.get("policy_valid") is False:
        if state.get("claimant_matches_policy_holder") is False:
            return {
                "decision": "denied",
                "decision_reason": "Claimant name must exactly match the policy holder name for this policy.",
                "payout_amount": None,
            }
        return {
            "decision": "denied",
            "decision_reason": "Policy is invalid, inactive, or does not cover this incident type.",
            "payout_amount": None,
        }

    fraud_risk = (state.get("fraud_risk") or "").lower()
    fraud_flags = state.get("fraud_flags") or []

    if fraud_risk == "high":
        return {
            "decision": "denied",
            "decision_reason": f"High fraud risk detected. Flags: {', '.join(fraud_flags)}",
            "payout_amount": None,
        }

    if fraud_risk == "medium":
        return {
            "decision": "escalated",
            "decision_reason": "Medium fraud risk — requires human adjuster review.",
            "payout_amount": None,
        }

    estimated_repair_cost = float(state.get("estimated_repair_cost") or 0.0)
    coverage_limit = float(state.get("coverage_limit") or 0.0)

    if estimated_repair_cost > coverage_limit:
        return {
            "decision": "escalated",
            "decision_reason": f"Claim amount (${estimated_repair_cost:,.0f}) exceeds coverage limit (${coverage_limit:,.0f}).",
            "payout_amount": None,
        }

    try:
        system_prompt = _load_prompt()
        client = get_openai_client()
        completion = client.chat.completions.create(
            model=LLM_MODEL,
            temperature=0.1,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": "Claim context:\n" + json.dumps(state, default=str),
                },
            ],
        )

        raw = completion.choices[0].message.content or "{}"
        parsed = json.loads(_strip_code_fences(raw))

        decision = parsed.get("decision")
        decision_reason = parsed.get("decision_reason")
        deductible = float(state.get("deductible") or 0.0)

        payout_amount = None
        if decision == "approved":
            payout_amount = max(0.0, estimated_repair_cost - deductible)

        return {
            "decision": decision,
            "decision_reason": decision_reason,
            "payout_amount": payout_amount,
        }
    except (OpenAIError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        logging.warning("Adjudication AI unavailable, using deterministic fallback: %s", exc)
        deductible = float(state.get("deductible") or 0.0)
        payout_amount = max(0.0, estimated_repair_cost - deductible) if estimated_repair_cost > 0 else None
        return {
            "decision": "approved" if estimated_repair_cost <= coverage_limit else "escalated",
            "decision_reason": "Automated fallback decision used due to adjudication model unavailability.",
            "payout_amount": payout_amount,
        }
