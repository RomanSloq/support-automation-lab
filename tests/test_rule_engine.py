import http.client
import json
import threading
import unittest
from http.server import HTTPServer

from src.api import RouteHandler
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


class ReservationSyncUnauthorizedRuleTest(unittest.TestCase):
    def test_active_401_routes_to_high_l2(self):
        result = evaluate_ticket(
            issue_type="reservation_sync",
            error_code=401,
            problem_active=True,
            affected_bookings=4,
            next_checkin_hours=12,
            affected_properties=1,
        )

        self.assertEqual(result, {"route": "L2", "priority": "High"})


class TicketCreatedWebhookTest(unittest.TestCase):
    def test_ticket_created_event_returns_engine_decision(self):
        server = HTTPServer(("127.0.0.1", 0), RouteHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port)
            event = {
                "event": "ticket.created",
                "ticket": {
                    "id": "T-100",
                    "affected_properties": 1,
                    "issue_type": "reservation_sync",
                    "affected_bookings": 1,
                    "other_bookings_working": True,
                },
            }
            connection.request(
                "POST",
                "/webhook/ticket-created",
                body=json.dumps(event),
                headers={"Content-Type": "application/json"},
            )
            response = connection.getresponse()
            result = json.loads(response.read())
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

        self.assertEqual(response.status, 200)
        self.assertEqual(
            result,
            {
                "received": True,
                "ticket_id": "T-100",
                "decision": {"route": "L1", "priority": "Normal"},
            },
        )


class ManualAiPageTest(unittest.TestCase):
    def test_manual_ai_page_is_served(self):
        server = HTTPServer(("127.0.0.1", 0), RouteHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port)
            connection.request("GET", "/manual-ai")
            response = connection.getresponse()
            page = response.read().decode("utf-8")
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

        self.assertEqual(response.status, 200)
        self.assertIn("Скопировать запрос для ChatGPT", page)
        self.assertIn("/route", page)
        self.assertIn('"problem_active" to true only when', page)


if __name__ == "__main__":
    unittest.main()
