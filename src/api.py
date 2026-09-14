"""Minimal local HTTP API for the existing rule engine."""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from src.rule_engine import evaluate_ticket


class RouteHandler(BaseHTTPRequestHandler):
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
        if self.path not in ("/route", "/webhook/ticket-created"):
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length))

        if self.path == "/webhook/ticket-created":
            if payload.get("event") != "ticket.created":
                self.send_error(400, "expected event ticket.created")
                return
            ticket = payload.get("ticket", {})
            ticket_id = ticket.get("id")
            ticket_facts = {key: value for key, value in ticket.items() if key != "id"}
            result = {
                "received": True,
                "ticket_id": ticket_id,
                "decision": evaluate_ticket(**ticket_facts),
            }
        else:
            result = evaluate_ticket(**payload)

        response = json.dumps(result).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

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
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped.", flush=True)
    finally:
        server.server_close()
