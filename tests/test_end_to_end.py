import http.client
import json
import threading
import unittest
from http.server import HTTPServer

from src.api import RouteHandler


class EndToEndFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), RouteHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def post_json(self, path, payload):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port)
        connection.request(
            "POST",
            path,
            body=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        return response.status, json.loads(response.read())

    def test_local_safe_case(self):
        status, result = self.post_json(
            "/route",
            {
                "affected_properties": 1,
                "issue_type": "reservation_sync",
                "affected_bookings": 1,
                "other_bookings_working": True,
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["route"], "L1")
        self.assertEqual(result["priority"], "Normal")
        self.assertFalse(result["human_review_required"])

    def test_mass_incident_case(self):
        status, result = self.post_json(
            "/route",
            {
                "affected_properties": 3,
                "issue_type": "availability_sync",
                "overbooking_risk": True,
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["route"], "Incident")
        self.assertEqual(result["priority"], "Critical")
        self.assertFalse(result["human_review_required"])

    def test_insufficient_facts_case(self):
        status, result = self.post_json(
            "/route",
            {
                "issue_type": None,
                "affected_properties": None,
                "affected_bookings": None,
                "claimed_urgency": "high",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["route"], "Clarify")
        self.assertIsNone(result["priority"])
        self.assertFalse(result["human_review_required"])

    def test_risky_duplicate_case(self):
        status, result = self.post_json(
            "/route",
            {
                "issue_type": "suspected_duplicate_booking",
                "affected_bookings": 2,
                "next_checkin_hours": 0,
                "problem_active": True,
                "claimed_urgency": "high",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result, {
            "route": "L2",
            "priority": "High",
            "human_review_required": True,
        })

    def test_webhook_and_manual_page(self):
        status, result = self.post_json(
            "/webhook/ticket-created",
            {
                "event": "ticket.created",
                "ticket": {
                    "id": "T-100",
                    "affected_properties": 1,
                    "issue_type": "reservation_sync",
                    "affected_bookings": 1,
                    "other_bookings_working": True,
                },
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["ticket_id"], "T-100")
        self.assertEqual(result["decision"]["route"], "L1")

        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port)
        connection.request("GET", "/manual-ai")
        page_response = connection.getresponse()
        self.assertEqual(page_response.status, 200)
        self.assertIn("Manual AI Test Harness", page_response.read().decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
