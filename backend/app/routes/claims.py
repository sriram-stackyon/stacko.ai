"""Claims API routes for submitting and retrieving claims."""

import base64
import json
import logging
import smtplib
from typing import Any
from email.message import EmailMessage
from email.utils import formataddr

import psycopg2
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.agents.pipeline import pipeline
from app.agents.state import ClaimsState
from app.config import (
    EMAIL_FROM_NAME,
    SMTP_FROM_EMAIL,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USE_TLS,
    SMTP_USER,
    get_db_connection,
)
from app.models import ClaimResultResponse, ClaimSummaryResponse

router = APIRouter()


def _send_claim_result_email(recipient_email: str, subject: str, body: str) -> None:
    """Send claim result email using centralized SMTP config."""
    if not SMTP_HOST or not SMTP_FROM_EMAIL:
        logging.warning("SMTP is not configured. Skipping claim result email to %s", recipient_email)
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr((EMAIL_FROM_NAME, SMTP_FROM_EMAIL))
    message["To"] = recipient_email
    if SMTP_USER:
        message["Reply-To"] = SMTP_USER
    message.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            if SMTP_USE_TLS:
                server.starttls()
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(message)
        logging.info("Claim result email sent successfully to %s", recipient_email)
    except (smtplib.SMTPException, TimeoutError, OSError) as exc:
        logging.error("Failed to send claim result email to %s: %s", recipient_email, exc)


def _to_float(value: Any) -> float | None:
    """Convert numeric values to float when possible."""
    if value is None:
        return None
    return float(value)


def _build_claim_response(row: dict[str, Any]) -> ClaimResultResponse:
    """Build detailed API response model from a claims table row."""
    return ClaimResultResponse(
        id=row["id"],
        policy_number=row.get("policy_number", ""),
        claimant_name=row.get("claimant_name", ""),
        incident_type=row.get("incident_type", ""),
        decision=row.get("decision"),
        payout_amount=_to_float(row.get("payout_amount")),
        fraud_risk=row.get("fraud_risk"),
        damage_severity=row.get("damage_severity"),
        created_at=row["created_at"],
        incident_description=row.get("incident_description", ""),
        photo_urls=row.get("photo_urls") or [],
        policy_valid=row.get("policy_valid"),
        policy_holder_name=row.get("policy_holder_name"),
        coverage_type=row.get("coverage_type"),
        coverage_limit=_to_float(row.get("coverage_limit")),
        deductible=_to_float(row.get("deductible")),
        damage_description=row.get("damage_description"),
        estimated_repair_cost=_to_float(row.get("estimated_repair_cost")),
        fraud_flags=row.get("fraud_flags") or [],
        decision_reason=row.get("decision_reason"),
        email_draft=row.get("email_draft"),
        error=row.get("error"),
    )


@router.post("/claims", response_model=ClaimResultResponse)
async def submit_claim(
    policy_number: str = Form(...),
    claimant_name: str = Form(...),
    claimant_email: str = Form(...),
    incident_type: str = Form(...),
    incident_description: str = Form(...),
    photos: list[UploadFile] | None = File(default=None),
) -> ClaimResultResponse:
    """Submit a new claim, run the AI pipeline, and persist the result."""
    if photos and len(photos) > 3:
        raise HTTPException(status_code=422, detail="At most 3 photos are allowed.")

    incident_type = incident_type.strip().lower()

    # Convert photos to base64 data URLs for in-memory GPT vision processing
    photo_data_urls: list[str] = []
    photo_refs: list[str] = []
    for photo in photos or []:
        content = await photo.read()
        if content:
            mime = photo.content_type or "image/jpeg"
            b64 = base64.b64encode(content).decode("utf-8")
            photo_data_urls.append(f"data:{mime};base64,{b64}")
            photo_refs.append(photo.filename or f"photo-{len(photo_refs) + 1}.jpg")

    initial_state: ClaimsState = {
        "policy_number": policy_number,
        "claimant_name": claimant_name,
        "incident_type": incident_type,
        "incident_description": incident_description,
        "photo_urls": photo_data_urls,
        "error": None,
    }

    try:
        final_state = pipeline.invoke(initial_state)
    except (ValueError, TypeError, RuntimeError) as exc:
        logging.error("Pipeline execution failed: %s", exc)
        raise HTTPException(status_code=500, detail="Claims pipeline execution failed.") from exc

    _INSERT_SQL = """
        INSERT INTO claims (
            policy_number, claimant_name, incident_type, incident_description,
            photo_urls, policy_valid, policy_holder_name, coverage_type,
            coverage_limit, deductible, damage_description, estimated_repair_cost,
            damage_severity, fraud_risk, fraud_flags, decision, decision_reason,
            payout_amount, email_draft, error
        ) VALUES (
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s
        ) RETURNING *
    """
    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute(_INSERT_SQL, (
                    policy_number,
                    claimant_name,
                    incident_type,
                    incident_description,
                    json.dumps(photo_refs),
                    final_state.get("policy_valid"),
                    final_state.get("policy_holder_name"),
                    final_state.get("coverage_type"),
                    final_state.get("coverage_limit"),
                    final_state.get("deductible"),
                    final_state.get("damage_description"),
                    final_state.get("estimated_repair_cost"),
                    final_state.get("damage_severity"),
                    final_state.get("fraud_risk"),
                    json.dumps(final_state.get("fraud_flags") or []),
                    final_state.get("decision"),
                    final_state.get("decision_reason"),
                    final_state.get("payout_amount"),
                    final_state.get("email_draft"),
                    final_state.get("error"),
                ))
                row = dict(cur.fetchone())
        conn.close()
    except psycopg2.Error as exc:
        logging.error("Failed to persist claim result: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Database connection failed. Please verify your DATABASE_URL (host/user/password) and ensure the Supabase project is active.",
        ) from exc

    try:
        subject = f"Claim Result: {row.get('decision') or 'Pending'} ({policy_number})"
        email_body = (row.get("email_draft") or "").strip() or (
            f"Hello {claimant_name},\n\n"
            f"Your claim has been processed.\n"
            f"Decision: {row.get('decision') or 'pending'}\n"
            f"Reason: {row.get('decision_reason') or 'No additional details available.'}\n"
            f"Estimated Repair Cost: {row.get('estimated_repair_cost') or 0.0}\n"
            f"Payout: {row.get('payout_amount') if row.get('payout_amount') is not None else 'No payout applicable'}\n\n"
            "Regards,\nClaims Team"
        )
        _send_claim_result_email(claimant_email, subject, email_body)
    except (smtplib.SMTPException, TimeoutError, OSError, ValueError) as exc:
        logging.error("Failed to send claim result email to %s: %s", claimant_email, exc)

    return _build_claim_response(row)


@router.get("/claims", response_model=list[ClaimSummaryResponse])
def list_claims() -> list[ClaimSummaryResponse]:
    """Return all submitted claims ordered by newest first."""
    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM claims ORDER BY created_at DESC")
                rows = [dict(r) for r in cur.fetchall()]
        conn.close()
    except psycopg2.Error as exc:
        logging.error("Failed to list claims: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to fetch claims.") from exc

    return [
        ClaimSummaryResponse(
            id=row["id"],
            policy_number=row.get("policy_number", ""),
            claimant_name=row.get("claimant_name", ""),
            incident_type=row.get("incident_type", ""),
            decision=row.get("decision"),
            payout_amount=_to_float(row.get("payout_amount")),
            fraud_risk=row.get("fraud_risk"),
            damage_severity=row.get("damage_severity"),
            created_at=row["created_at"],
        )
        for row in rows
    ]


@router.get("/claims/{claim_id}", response_model=ClaimResultResponse)
def get_claim(claim_id: str) -> ClaimResultResponse:
    """Return full details for a single claim."""
    try:
        conn = get_db_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM claims WHERE id = %s LIMIT 1", (claim_id,))
                raw = cur.fetchone()
        conn.close()
    except psycopg2.Error as exc:
        logging.error("Failed to get claim %s: %s", claim_id, exc)
        raise HTTPException(status_code=500, detail="Failed to fetch claim.") from exc

    if not raw:
        raise HTTPException(status_code=404, detail="Claim not found.")

    return _build_claim_response(dict(raw))
