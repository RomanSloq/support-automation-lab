import http.client
import json
import threading
import unittest
from http.server import HTTPServer

from src.api import RouteHandler


class ApiValidationTest(unittest.TestCase):
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

    def post_raw(self, path, body):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port)
        connection.request(
            "POST",
            path,
            body=body,
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        payload = json.loads(response.read())
        return response.status, payload

    def test_malformed_json_and_non_object_are_400(self):
        for body, expected_error in (("{", "invalid_json"), ("[]", "json_object_required")):
            with self.subTest(body=body):
                status, payload = self.post_raw("/route", body)
                self.assertEqual(status, 400)
                self.assertEqual(payload["error"], expected_error)

    def test_wrong_types_and_unknown_issue_type_are_422(self):
        cases = (
            {"affected_properties": "3", "issue_type": "availability_sync"},
            {"affected_properties": 1, "issue_type": "mystery"},
            {"claimed_urgency": "urgent"},
        )
        for facts in cases:
            with self.subTest(facts=facts):
                status, payload = self.post_raw("/route", json.dumps(facts))
                self.assertEqual(status, 422)
                self.assertEqual(payload["error"], "invalid_ticket_facts")

    def test_missing_business_facts_still_route_to_clarify(self):
        for facts in ({}, {"issue_type": None, "affected_properties": None}):
            with self.subTest(facts=facts):
                status, payload = self.post_raw("/route", json.dumps(facts))
                self.assertEqual(status, 200)
                self.assertEqual(payload["route"], "Clarify")
                self.assertIsNone(payload["priority"])

    def test_webhook_rejects_invalid_envelopes(self):
        cases = (
            ({"event": "ticket.updated", "ticket": {}}, "expected_ticket_created_event"),
            ({"ticket": {}}, "expected_ticket_created_event"),
            ({"event": "ticket.created"}, "ticket_object_required"),
            ({"event": "ticket.created", "ticket": []}, "ticket_object_required"),
        )
        for event, expected_error in cases:
            with self.subTest(event=event):
                status, payload = self.post_raw(
                    "/webhook/ticket-created",
                    json.dumps(event),
                )
                self.assertEqual(status, 400)
                self.assertEqual(payload["error"], expected_error)


if __name__ == "__main__":
    unittest.main()
