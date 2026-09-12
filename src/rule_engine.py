"""Minimal rule engine prototype for three support cases."""


def evaluate_ticket(
    affected_properties,
    issue_type,
    overbooking_risk=None,
    affected_bookings=None,
    other_bookings_working=None,
    claimed_urgency=None,
):
    """Return routing for the supported rules."""
    if (
        affected_properties is None
        or issue_type is None
        or (
            issue_type == "availability_sync"
            and overbooking_risk is None
        )
        or (
            issue_type == "reservation_sync"
            and (
                affected_bookings is None
                or other_bookings_working is None
            )
        )
    ):
        return {"route": "Clarify", "priority": None}

    if (
        affected_properties >= 2
        and issue_type == "availability_sync"
        and overbooking_risk is True
    ):
        return {"route": "Incident", "priority": "Critical"}

    if (
        affected_properties == 1
        and issue_type == "reservation_sync"
        and affected_bookings == 1
        and other_bookings_working is True
    ):
        return {"route": "L1", "priority": "Normal"}

    return {"route": "Unmatched", "priority": "Normal"}


if __name__ == "__main__":
    ticket_facts = {
        "affected_properties": 3,
        "issue_type": "availability_sync",
        "overbooking_risk": True,
    }
    result = evaluate_ticket(**ticket_facts)
    print("input:", ticket_facts)
    print("output:", result)
