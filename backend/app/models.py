"""Pydantic API response models for claims endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import UUID4, BaseModel


class ClaimSummaryResponse(BaseModel):
    """Compact claim data returned for history listings."""

    id: UUID4
    policy_number: str
    claimant_name: str
    incident_type: str
    decision: Optional[str]
    payout_amount: Optional[float]
    fraud_risk: Optional[str]
    damage_severity: Optional[str]
    created_at: datetime


class ClaimResultResponse(ClaimSummaryResponse):
    """Detailed claim data returned after submission and detail retrieval."""

    incident_description: str
    photo_urls: list[str]
    policy_valid: Optional[bool]
    policy_holder_name: Optional[str] = None
    coverage_type: Optional[str]
    coverage_limit: Optional[float]
    deductible: Optional[float] = None
    damage_description: Optional[str]
    estimated_repair_cost: Optional[float]
    fraud_flags: Optional[list[str]]
    decision_reason: Optional[str]
    email_draft: Optional[str]
    error: Optional[str]
