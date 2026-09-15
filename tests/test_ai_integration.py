import http.client
import json
import threading
import unittest
from http.server import HTTPServer
from types import SimpleNamespace
from unittest.mock import Mock, patch

from src.ai_extractor import AIExtractorError, EXTRACTION_INSTRUCTIONS, ExtractionResult, extract_ticket
from src.api import RouteHandler


LOCAL_FACTS = {
    "affected_properties": None,
    "issue_type": "reservation_sync",
    "affected_bookings": 1,
    "other_bookings_working": None,
    "overbooking_risk": None,
    "error_code": None,
    "problem_active": None,
    "next_checkin_hours": None,
    "claimed_urgency": None,
}

SYNTHETIC_USAGE = SimpleNamespace(
    input_tokens=1_000_000,
    input_tokens_details=SimpleNamespace(cached_tokens=200_000, cache_write_tokens=100_000),
    output_tokens=500_000,
    output_tokens_details=SimpleNamespace(reasoning_tokens=0),
    total_tokens=1_500_000,
)

EXPECTED_USAGE = {
    "model": "gpt-5.6-luna",
    "input_tokens": 1_000_000,
    "cached_input_tokens": 200_000,
    "cache_write_tokens": 100_000,
    "uncached_input_tokens": 700_000,
    "output_tokens": 500_000,
    "reasoning_tokens": 0,
    "total_tokens": 1_500_000,
    "estimated_cost_usd": 0.769,
}


class AIExtractorTest(unittest.TestCase):
    def test_responses_api_uses_strict_schema_and_safe_settings(self):
        response = SimpleNamespace(
            status="completed",
            output_text=json.dumps(LOCAL_FACTS),
            output=[],
            usage=SYNTHETIC_USAGE,
            model="gpt-5.6-luna",
        )
        client = SimpleNamespace(responses=SimpleNamespace(create=Mock(return_value=response)))

        extraction = extract_ticket("Одна бронь Booking не появилась в PMS.", client=client)

        self.assertEqual(extraction.facts, LOCAL_FACTS)
        call = client.responses.create.call_args.kwargs
        self.assertEqual(call["model"], "gpt-5.6-luna")
        self.assertFalse(call["store"])
        self.assertEqual(call["reasoning"], {"effort": "none"})
        self.assertTrue(call["text"]["format"]["strict"])
        self.assertFalse(call["text"]["format"]["schema"]["additionalProperties"])
        self.assertIn("never choose a\nclosest match", EXTRACTION_INSTRUCTIONS)
        self.assertIn("generic problem\nwith a rate plan is not availability_sync", EXTRACTION_INSTRUCTIONS)
        self.assertIn('"сейчас не могу..."', EXTRACTION_INSTRUCTIONS)
        self.assertIn('explicitly says the problem was resolved, stopped, or is no longer observed', EXTRACTION_INSTRUCTIONS)
        self.assertIn('A past event without a clear current-state signal remains null', EXTRACTION_INSTRUCTIONS)
        self.assertIn("right now, or immediately", EXTRACTION_INSTRUCTIONS)
        self.assertIn('"Today" alone\ndoes not establish 0', EXTRACTION_INSTRUCTIONS)

    def test_problem_active_prompt_boundary_is_general(self):
        self.assertIn("present/current state", EXTRACTION_INSTRUCTIONS)
        self.assertIn('"сейчас не работает"', EXTRACTION_INSTRUCTIONS)
        self.assertIn('"прямо сейчас..."', EXTRACTION_INSTRUCTIONS)
        self.assertIn('"получаем ошибку сейчас"', EXTRACTION_INSTRUCTIONS)
        self.assertIn("otherwise return null", EXTRACTION_INSTRUCTIONS)

    def test_usage_metadata_and_luna_cost_estimate(self):
        response = SimpleNamespace(
            status="completed",
            output_text=json.dumps(LOCAL_FACTS),
            output=[],
            usage=SYNTHETIC_USAGE,
            model="gpt-5.6-luna",
        )
        client = SimpleNamespace(responses=SimpleNamespace(create=Mock(return_value=response)))

        extraction = extract_ticket("Текст тикета", client=client)

        self.assertEqual(extraction.usage, EXPECTED_USAGE)

    def test_incomplete_refused_and_invalid_responses_are_technical_failures(self):
        responses = (
            (SimpleNamespace(status="incomplete", output_text="", output=[]), "incomplete_response"),
            (
                SimpleNamespace(
                    status="completed",
                    output_text="",
                    output=[SimpleNamespace(content=[SimpleNamespace(type="refusal", refusal="no")])],
                ),
                "refused_response",
            ),
            (SimpleNamespace(status="completed", output_text="not-json", output=[]), "invalid_response"),
            (SimpleNamespace(status="completed", output_text="{}", output=[]), "invalid_response"),
        )
        for response, expected_code in responses:
            with self.subTest(expected_code=expected_code):
                client = SimpleNamespace(
                    responses=SimpleNamespace(create=Mock(return_value=response))
                )
                with self.assertRaises(AIExtractorError) as raised:
                    extract_ticket("Текст тикета", client=client)
                self.assertEqual(raised.exception.code, expected_code)


class AIRouteEndpointTest(unittest.TestCase):
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

    def post(self, payload):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port)
        connection.request(
            "POST",
            "/ai/route",
            body=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        return response.status, json.loads(response.read())

    def test_ai_route_passes_extracted_facts_to_rule_engine(self):
        with patch(
            "src.api.extract_ticket",
            return_value=ExtractionResult(facts=LOCAL_FACTS, usage=EXPECTED_USAGE),
        ):
            status, payload = self.post({"text": "Одна бронь Booking не появилась в PMS."})

        self.assertEqual(status, 200)
        self.assertEqual(payload["facts"], LOCAL_FACTS)
        self.assertEqual(payload["usage"], EXPECTED_USAGE)
        self.assertEqual(
            payload["decision"],
            {
                "route": "Clarify",
                "priority": None,
                "human_review_required": False,
            },
        )

    def test_empty_text_is_400_without_calling_ai(self):
        with patch("src.api.extract_ticket") as extractor:
            status, payload = self.post({"text": "   "})

        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "empty_text")
        extractor.assert_not_called()

    def test_openai_failures_remain_technical_failures(self):
        expected_status = {
            "missing_api_key": 503,
            "authentication_failed": 502,
            "quota_or_rate_limit": 429,
            "network_error": 502,
            "api_error": 502,
            "incomplete_response": 502,
            "refused_response": 502,
            "invalid_response": 502,
        }
        for code, status_code in expected_status.items():
            with self.subTest(code=code):
                with patch("src.api.extract_ticket", side_effect=AIExtractorError(code)):
                    status, payload = self.post({"text": "Текст тикета"})
                self.assertEqual(status, status_code)
                self.assertEqual(payload, {"error": code})


if __name__ == "__main__":
    unittest.main()
