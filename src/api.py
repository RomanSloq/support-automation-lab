"""Minimal local HTTP API for the existing rule engine."""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from src.rule_engine import evaluate_ticket


class RouteHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/route":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", 0))
        ticket_facts = json.loads(self.rfile.read(length))
        result = evaluate_ticket(**ticket_facts)
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
    server.serve_forever()
