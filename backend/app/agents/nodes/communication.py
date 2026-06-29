"""Customer communication drafting node."""

import logging
import re
from pathlib import Path

from openai import OpenAIError

from app.agents.state import ClaimsState
from app.config import LLM_MODEL, get_openai_client

SUPPORT_EMAIL = "india.support@stackoai.com"


def _load_prompt() -> str:
    """Load the communication system prompt from disk."""
    prompt_path = Path(__file__).resolve().parents[2] / "prompts" / "communication_system.txt"
    return prompt_path.read_text(encoding="utf-8")


def _build_fallback_email(state: ClaimsState, holder_name: str, payout_text: str) -> str:
    """Build a deterministic, complete fallback email body."""
    decision = (state.get("decision") or "pending").strip().lower()
    reason = state.get("decision_reason") or "Further review details are not available at this time."
    incident = state.get("incident_type") or "the reported incident"

    if decision == "approved":
        decision_section = (
            f"We are pleased to inform you that your claim for {incident} has been approved. "
            f"Your estimated payout is {payout_text}, subject to final policy verification."
        )
        next_steps = (
            "Our payments team will process this amount and contact you shortly with transfer details."
        )
    elif decision == "denied":
        decision_section = (
            f"After reviewing your claim for {incident}, we are unable to approve it at this time."
        )
        next_steps = (
            "If you would like this decision reviewed, please reply with any supporting documents and "
            "our team will initiate an appeal review."
        )
    elif decision == "escalated":
        decision_section = (
            f"Your claim for {incident} requires additional review by a human adjuster."
        )
        next_steps = "A claims specialist will contact you within 3 business days with the next steps."
    else:
        decision_section = f"Your claim for {incident} is currently under review."
        next_steps = "We will share the final decision as soon as the review is complete."

    return (
        f"Dear {holder_name},\n\n"
        f"{decision_section}\n\n"
        f"Reason: {reason}\n"
        f"Payout: {payout_text}.\n\n"
        f"{next_steps}\n\n"
        "Thank you for your patience and cooperation.\n\n"
        "Regards,\n"
        "Claims Team"
    )


def _sanitize_email_body(raw_body: str) -> str:
    """Normalize generated email body into plain text."""
    body = (raw_body or "").strip()
    body = re.sub(r"^```[a-zA-Z]*\s*", "", body)
    body = re.sub(r"\s*```$", "", body)
    return body.strip()


def _append_support_footer(email_body: str) -> str:
    """Append support contact footer when it is missing."""
    body = (email_body or "").rstrip()
    if SUPPORT_EMAIL.lower() in body.lower():
        return body
    return f"{body}\n\n{SUPPORT_EMAIL}"


def _is_usable_email_draft(email_body: str, holder_name: str) -> bool:
    """Check whether the generated draft is complete enough to send."""
    body = (email_body or "").strip()
    if len(body) < 120:
        return False

    lowered = body.lower()
    has_closing = ("regards" in lowered) or ("sincerely" in lowered) or ("claims team" in lowered)
    has_name = holder_name.lower() in lowered or "dear" in lowered
    return has_closing and has_name


def communication_node(state: ClaimsState) -> dict:
    """Generate a plain-text customer email draft from claim decision details."""
    if state.get("error"):
        return {}

    holder_name = state.get("policy_holder_name") or state.get("claimant_name") or "Customer"
    payout_text = (
        f"${float(state.get('payout_amount') or 0.0):,.2f}"
        if state.get("payout_amount") is not None
        else "no payout"
    )

    fallback_email = _append_support_footer(
        _build_fallback_email(state, holder_name, payout_text)
    )

    try:
        client = get_openai_client()
        system_prompt = _load_prompt()
        user_prompt = (
            f"Claimant: {holder_name}\n"
            f"Incident type: {state.get('incident_type')}\n"
            f"Decision: {state.get('decision')}\n"
            f"Reason: {state.get('decision_reason')}\n"
            f"Payout: {payout_text}"
        )

        completion = client.chat.completions.create(
            model=LLM_MODEL,
            temperature=0.3,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        finish_reason = completion.choices[0].finish_reason
        email_draft = _sanitize_email_body(completion.choices[0].message.content or "")
        if finish_reason == "length" or not _is_usable_email_draft(email_draft, holder_name):
            logging.warning("Communication draft incomplete, using deterministic fallback.")
            return {"email_draft": fallback_email}

        return {"email_draft": _append_support_footer(email_draft)}
    except (OpenAIError, ValueError, KeyError, TypeError) as exc:
        logging.warning("Communication generation unavailable, using fallback draft: %s", exc)
        return {"email_draft": fallback_email}
