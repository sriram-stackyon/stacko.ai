"""Damage assessment node using GPT-4o vision."""

import json
import logging
import re
from pathlib import Path

from openai import OpenAIError

from app.agents.state import ClaimsState
from app.config import LLM_MODEL, get_openai_client


def _load_prompt() -> str:
    """Load the damage assessment system prompt from disk."""
    prompt_path = Path(__file__).resolve().parents[2] / "prompts" / "damage_assessment_system.txt"
    return prompt_path.read_text(encoding="utf-8")


def _strip_code_fences(raw: str) -> str:
    """Remove optional markdown code fences from LLM output."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    return cleaned.strip()


def _extract_json_payload(raw: str) -> dict:
    """Extract a JSON object from model output, even if extra text is present."""
    cleaned = _strip_code_fences(raw)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if match:
        candidate = match.group(0)
        return json.loads(candidate)

    raise json.JSONDecodeError("Could not extract JSON payload", cleaned, 0)


def _normalize_severity(severity: str | None) -> str:
    """Normalize model output to one of the allowed severity labels."""
    value = (severity or "low").strip().lower()
    if value not in {"low", "medium", "high"}:
        return "low"
    return value


def _fallback_damage_assessment(state: ClaimsState) -> dict:
    """Estimate damage from claim text when vision parsing is unavailable."""
    incident_type = (state.get("incident_type") or "").strip().lower()
    description = (state.get("incident_description") or "").strip().lower()
    photo_count = len(state.get("photo_urls") or [])

    base_cost_map = {
        "fire": 3500.0,
        "collision": 2800.0,
        "third-party": 2000.0,
        "theft": 1800.0,
        "weather": 2200.0,
        "vandalism": 1200.0,
    }
    cost = base_cost_map.get(incident_type, 1500.0)
    severity = "low"

    high_keywords = {"total", "severe", "major", "extensive", "burned", "burnt", "structural", "inoperable"}
    medium_keywords = {"damage", "dented", "broken", "cracked", "smoke", "rear", "bumper", "trunk", "taillight", "taillights", "windshield", "hood", "door", "fender"}
    low_keywords = {"minor", "scratch", "scratched", "small", "light", "scuff", "scuffed", "chip", "chiping", "chips"}

    if any(keyword in description for keyword in high_keywords):
        severity = "high"
        cost *= 2.2
    elif any(keyword in description for keyword in medium_keywords):
        severity = "medium"
        cost *= 1.35
    elif any(keyword in description for keyword in low_keywords):
        severity = "low"
        cost *= 0.75

    if photo_count >= 3:
        cost *= 1.15
    elif photo_count == 2:
        cost *= 1.08
    elif photo_count == 1:
        cost *= 1.03

    if severity == "low" and cost >= 2500:
        severity = "medium"
    if severity == "medium" and cost >= 7000:
        severity = "high"

    return {
        "damage_description": "Damage analysis unavailable; estimate derived from claim details.",
        "estimated_repair_cost": round(cost, 2),
        "damage_severity": severity,
    }


def damage_assessment_node(state: ClaimsState) -> dict:
    """Analyze submitted claim photos and estimate repair cost."""
    if state.get("error"):
        return {}

    photo_urls = state.get("photo_urls") or []
    if not photo_urls:
        return {
            "damage_description": "No photos provided",
            "estimated_repair_cost": 0.0,
            "damage_severity": "low",
        }

    try:
        system_prompt = _load_prompt()
        client = get_openai_client()
        user_content = [{"type": "text", "text": "Analyze all provided damage photos."}]
        user_content.extend(
            [{"type": "image_url", "image_url": {"url": url}} for url in photo_urls]
        )

        completion = client.chat.completions.create(
            model=LLM_MODEL,
            temperature=0.2,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        )

        raw = completion.choices[0].message.content or "{}"
        parsed = _extract_json_payload(raw)

        return {
            "damage_description": parsed.get("damage_description"),
            "estimated_repair_cost": float(parsed.get("estimated_repair_cost", 0.0)),
            "damage_severity": _normalize_severity(parsed.get("damage_severity")),
        }
    except (OpenAIError, ValueError, KeyError, json.JSONDecodeError, TypeError) as exc:
        logging.warning("Damage assessment unavailable, using fallback values: %s", exc)
        return _fallback_damage_assessment(state)
