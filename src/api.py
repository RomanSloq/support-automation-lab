"""Minimal local HTTP API for the existing rule engine."""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from src.ai_extractor import AIExtractorError, extract_ticket
from src.rule_engine import evaluate_ticket
from src.ticket_contract import validate_ticket_facts


class RouteHandler(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        response = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def read_json_object(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length))
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            self.send_json(400, {"error": "invalid_json"})
            return None

        if not isinstance(payload, dict):
            self.send_json(400, {"error": "json_object_required"})
            return None
        return payload

    def route_facts(self, facts):
        try:
            validate_ticket_facts(facts)
        except ValueError as error:
            self.send_json(422, {"error": "invalid_ticket_facts", "detail": str(error)})
            return
        self.send_json(200, evaluate_ticket(**facts))

    def do_GET(self):
        if self.path != "/manual-ai":
            self.send_error(404)
            return

        page = Path(__file__).with_name("manual_ai.html").read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page)

    def do_POST(self):
        if self.path not in ("/route", "/webhook/ticket-created", "/ai/route"):
            self.send_error(404)
            return

        payload = self.read_json_object()
        if payload is None:
            return

        if self.path == "/webhook/ticket-created":
            if payload.get("event") != "ticket.created":
                self.send_json(400, {"error": "expected_ticket_created_event"})
                return
            ticket = payload.get("ticket")
            if not isinstance(ticket, dict):
                self.send_json(400, {"error": "ticket_object_required"})
                return
            ticket_id = ticket.get("id")
            ticket_facts = {key: value for key, value in ticket.items() if key != "id"}
            try:
                validate_ticket_facts(ticket_facts)
            except ValueError as error:
                self.send_json(
                    422,
                    {"error": "invalid_ticket_facts", "detail": str(error)},
                )
                return
            result = {
                "received": True,
                "ticket_id": ticket_id,
                "decision": evaluate_ticket(**ticket_facts),
            }
            self.send_json(200, result)
            return

        if self.path == "/ai/route":
            if set(payload) != {"text"} or not isinstance(payload.get("text"), str):
                self.send_json(400, {"error": "text_string_required"})
                return
            if not payload["text"].strip():
                self.send_json(400, {"error": "empty_text"})
                return
            try:
                extraction = extract_ticket(payload["text"])
            except AIExtractorError as error:
                status_by_code = {
                    "missing_api_key": 503,
                    "sdk_unavailable": 503,
                    "authentication_failed": 502,
                    "quota_or_rate_limit": 429,
                    "network_error": 502,
                    "api_error": 502,
                    "incomplete_response": 502,
                    "refused_response": 502,
                    "invalid_response": 502,
                }
                self.send_json(
                    status_by_code.get(error.code, 502),
                    {"error": error.code},
                )
                return
            self.send_json(
                200,
                {
                    "facts": extraction.facts,
                    "decision": evaluate_ticket(**extraction.facts),
                    "usage": extraction.usage,
                },
            )
            return

        self.route_facts(payload)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8000), RouteHandler)
    print("Serving POST /route at http://127.0.0.1:8000/route", flush=True)
    print(
        "Serving POST /webhook/ticket-created at "
        "http://127.0.0.1:8000/webhook/ticket-created",
        flush=True,
    )
    print("Serving POST /ai/route at http://127.0.0.1:8000/ai/route", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped.", flush=True)
    finally:
        server.server_close()
