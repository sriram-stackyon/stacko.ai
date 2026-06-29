"""Input validation node."""

from app.agents.state import ClaimsState


def intake_node(state: ClaimsState) -> dict:
    """Validate required claim input fields before processing."""
    required_fields = [
        "policy_number",
        "claimant_name",
        "incident_type",
        "incident_description",
    ]

    for field in required_fields:
        value = state.get(field)
        if not isinstance(value, str) or not value.strip():
            return {"error": f"Missing required field: {field}"}

    return {}
