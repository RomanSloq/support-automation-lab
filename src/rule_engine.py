"""Minimal rule engine prototype with a human-review gate."""


def evaluate_ticket(
    affected_properties=None,
    issue_type=None,
    overbooking_risk=None,
    affected_bookings=None,
    other_bookings_working=None,
    claimed_urgency=None,
    error_code=None,
    problem_active=None,
    next_checkin_hours=None,
):
    """Return routing for the supported rules."""
    if (
        issue_type == "suspected_duplicate_booking"
        and affected_bookings is not None
        and next_checkin_hours == 0
        and problem_active is True
    ):
        return {
            "route": "L2",
            "priority": "High",
            "human_review_required": True,
        }

    if (
        issue_type == "reservation_sync"
        and error_code == 401
        and problem_active is True
    ):
        return {
            "route": "L2",
            "priority": "High",
            "human_review_required": False,
        }

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
        return {
            "route": "Clarify",
            "priority": None,
            "human_review_required": False,
        }

    if (
        affected_properties >= 2
        and issue_type == "availability_sync"
        and overbooking_risk is True
    ):
        return {
            "route": "Incident",
            "priority": "Critical",
            "human_review_required": False,
        }

    if (
        affected_properties == 1
        and issue_type == "reservation_sync"
        and affected_bookings == 1
        and other_bookings_working is True
    ):
        return {
            "route": "L1",
            "priority": "Normal",
            "human_review_required": False,
        }

    return {
        "route": "Unmatched",
        "priority": "Normal",
        "human_review_required": False,
    }


if __name__ == "__main__":
    ticket_facts = {
        "affected_properties": 3,
        "issue_type": "availability_sync",
        "overbooking_risk": True,
    }
    result = evaluate_ticket(**ticket_facts)
    print("input:", ticket_facts)
    print("output:", result)
