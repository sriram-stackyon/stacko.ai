"""Typed state contract for the claims processing graph."""

from typing import Optional, TypedDict


class ClaimsState(TypedDict, total=False):
    """State object passed between all nodes in the claims pipeline."""

    policy_number: str
    claimant_name: str
    incident_type: str
    incident_description: str
    photo_urls: list[str]

    policy_valid: Optional[bool]
    policy_holder_name: Optional[str]
    claimant_matches_policy_holder: Optional[bool]
    coverage_type: Optional[str]
    coverage_limit: Optional[float]
    deductible: Optional[float]

    damage_description: Optional[str]
    estimated_repair_cost: Optional[float]
    damage_severity: Optional[str]

    fraud_risk: Optional[str]
    fraud_flags: Optional[list[str]]

    decision: Optional[str]
    decision_reason: Optional[str]
    payout_amount: Optional[float]

    email_draft: Optional[str]

    error: Optional[str]
