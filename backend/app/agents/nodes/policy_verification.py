"""Policy validation node."""

from datetime import date, datetime
import logging

import psycopg2
from app.agents.state import ClaimsState
from app.config import get_db_connection


def _normalize_label(value: str) -> str:
    """Normalize incident/coverage labels into canonical values."""
    cleaned = (value or "").strip().lower().replace("_", "-")
    aliases = {
        "thirdparty": "third-party",
        "third party": "third-party",
        "liability": "third-party",
    }
    return aliases.get(cleaned, cleaned)


def _normalize_person_name(value: str) -> str:
    """Normalize person names for robust equality checks."""
    return " ".join((value or "").strip().casefold().split())


def _incident_is_covered(incident_type: str, coverage_type: str) -> bool:
    """Check if incident type is covered by policy coverage type."""
    incident = _normalize_label(incident_type)
    coverage = _normalize_label(coverage_type)

    covered_incidents_by_policy = {
        "collision": {"collision"},
        "third-party": {"collision", "third-party"},
        "fire": {"fire"},
        "comprehensive": {"collision", "third-party", "theft", "fire", "weather", "vandalism"},
    }
    return incident in covered_incidents_by_policy.get(coverage, set())


def policy_verification_node(state: ClaimsState) -> dict:
    """Validate policy status, holder identity, and coverage for the incident type."""
    if state.get("error"):
        return {}

    policy_number = (state.get("policy_number") or "").strip()
    incident_type = _normalize_label(state.get("incident_type") or "")

    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM policies WHERE policy_number = %s LIMIT 1",
                    (policy_number,),
                )
                raw = cur.fetchone()
        conn.close()
        rows = [dict(raw)] if raw else []
    except psycopg2.Error as exc:
        logging.error("Policy lookup failed: %s", exc)
        return {"error": "Policy verification failed."}

    if not rows:
        logging.info("Policy not found for policy_number=%s", policy_number)
        return {"policy_valid": False}

    policy = rows[0]
    is_active = bool(policy.get("is_active"))

    expiry_raw = policy.get("expiry_date")
    try:
        if isinstance(expiry_raw, date):
            expiry_date = expiry_raw
        else:
            expiry_date = datetime.fromisoformat(str(expiry_raw)).date()
    except ValueError:
        logging.error("Invalid expiry date for policy_number=%s", policy_number)
        return {"policy_valid": False}

    claimant_name = state.get("claimant_name") or ""
    holder_name = str(policy.get("holder_name") or "")
    if _normalize_person_name(claimant_name) != _normalize_person_name(holder_name):
        logging.info(
            "Claimant name mismatch for policy_number=%s (claimant=%s, holder=%s)",
            policy_number,
            claimant_name,
            holder_name,
        )
        return {
            "policy_valid": False,
            "policy_holder_name": holder_name,
            "claimant_matches_policy_holder": False,
        }

    coverage_type = _normalize_label(str(policy.get("coverage_type") or ""))
    valid = is_active and expiry_date >= date.today() and _incident_is_covered(incident_type, coverage_type)

    if not valid:
        logging.info("Policy invalid for policy_number=%s", policy_number)
        return {"policy_valid": False}

    return {
        "policy_valid": True,
        "policy_holder_name": policy.get("holder_name"),
        "claimant_matches_policy_holder": True,
        "coverage_type": policy.get("coverage_type"),
        "coverage_limit": float(policy.get("coverage_limit")) if policy.get("coverage_limit") is not None else None,
        "deductible": float(policy.get("deductible")) if policy.get("deductible") is not None else None,
    }
