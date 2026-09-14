# Ticket-created webhook

The local server exposes one webhook receiver:

```text
POST http://127.0.0.1:8000/webhook/ticket-created
```

It accepts an event with `event = "ticket.created"` and a nested `ticket` object. The webhook extracts the ticket facts and passes them to the existing `rule_engine.py`. It contains no routing rules of its own.

Postman is used here as an imitation of an external HelpDesk system. In a real integration, the HelpDesk would send this event automatically when a ticket is created. This project does not yet claim to have a real HelpDesk integration.
