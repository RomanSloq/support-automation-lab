"""Shared structured-facts contract for HTTP input and AI output."""

FACT_FIELDS = (
    "affected_properties",
    "issue_type",
    "affected_bookings",
    "other_bookings_working",
    "overbooking_risk",
    "error_code",
    "problem_active",
    "next_checkin_hours",
    "claimed_urgency",
)

SUPPORTED_ISSUE_TYPES = (
    "availability_sync",
    "reservation_sync",
    "suspected_duplicate_booking",
)

INTEGER_FIELDS = {
    "affected_properties",
    "affected_bookings",
    "error_code",
    "next_checkin_hours",
}

BOOLEAN_FIELDS = {
    "other_bookings_working",
    "overbooking_risk",
    "problem_active",
}

TICKET_FACTS_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "affected_properties": {"type": ["integer", "null"], "minimum": 0},
        "issue_type": {
            "type": ["string", "null"],
            "enum": [*SUPPORTED_ISSUE_TYPES, None],
        },
        "affected_bookings": {"type": ["integer", "null"], "minimum": 0},
        "other_bookings_working": {"type": ["boolean", "null"]},
        "overbooking_risk": {"type": ["boolean", "null"]},
        "error_code": {"type": ["integer", "null"], "minimum": 0},
        "problem_active": {"type": ["boolean", "null"]},
        "next_checkin_hours": {"type": ["integer", "null"], "minimum": 0},
        "claimed_urgency": {
            "type": ["string", "null"],
            "enum": ["low", "normal", "high", None],
        },
    },
    "required": list(FACT_FIELDS),
    "additionalProperties": False,
}


def validate_ticket_facts(facts):
    """Validate supplied facts while allowing missing and null business facts."""
    unknown_fields = set(facts) - set(FACT_FIELDS)
    if unknown_fields:
        raise ValueError(f"unknown fields: {', '.join(sorted(unknown_fields))}")

    for field, value in facts.items():
        if value is None:
            continue
        if field in INTEGER_FIELDS and (type(value) is not int or value < 0):
            raise ValueError(f"{field} must be a non-negative integer or null")
        if field in BOOLEAN_FIELDS and type(value) is not bool:
            raise ValueError(f"{field} must be a boolean or null")
        if field == "issue_type" and value not in SUPPORTED_ISSUE_TYPES:
            raise ValueError("issue_type is not supported")
        if field == "claimed_urgency" and value not in ("low", "normal", "high"):
            raise ValueError("claimed_urgency must be low, normal, high, or null")

    return facts
