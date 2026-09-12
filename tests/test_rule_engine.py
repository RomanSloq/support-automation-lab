import unittest

from src.rule_engine import evaluate_ticket


class AvailabilitySyncIncidentRuleTest(unittest.TestCase):
    def test_matching_ticket_routes_to_critical_incident(self):
        result = evaluate_ticket(
            affected_properties=3,
            issue_type="availability_sync",
            overbooking_risk=True,
        )

        self.assertEqual(
            result,
            {"route": "Incident", "priority": "Critical"},
        )


class ReservationSyncLocalRuleTest(unittest.TestCase):
    def test_matching_ticket_routes_to_normal_l1(self):
        result = evaluate_ticket(
            affected_properties=1,
            issue_type="reservation_sync",
            affected_bookings=1,
            other_bookings_working=True,
        )

        self.assertEqual(
            result,
            {"route": "L1", "priority": "Normal"},
        )


class InsufficientFactsRuleTest(unittest.TestCase):
    def test_emotional_urgency_without_facts_routes_to_clarify(self):
        result = evaluate_ticket(
            affected_properties=None,
            issue_type=None,
            affected_bookings=None,
            claimed_urgency="high",
        )

        self.assertEqual(result, {"route": "Clarify", "priority": None})


if __name__ == "__main__":
    unittest.main()
