# End-to-end verification

## Automated local flow

Structured facts or an external `ticket.created` event go through the existing local API, then `rule_engine.py`, and return `route`, `priority`, and `human_review_required`:

```text
input facts/event → API or webhook → rule_engine.py → decision
```

The verified cases are:

1. Local safe reservation issue → `L1` / `Normal` / review `false`.
2. Mass availability issue with overbooking risk → `Incident` / `Critical` / review `false`.
3. Missing facts with claimed urgency → `Clarify` / no priority / review `false`.
4. Suspected duplicate booking with check-in now → `L2` / `High` / review `true`.

The webhook flow was also verified: `ticket.created` event → nested ticket facts → rule engine → decision. `GET /manual-ai` returned `200`.

## Manual AI-assisted flow

The Manual AI Test Harness is not an automated OpenAI integration. The user copies a prompt to ChatGPT manually, receives facts JSON, pastes it back, and the page sends it to the existing `/route` endpoint. ChatGPT extracts facts only; the rule engine chooses the decision.

Two manual extraction checks were confirmed:

- Three hotels with availability sync and overbooking concern → facts produced `Incident` / `Critical`.
- One booking missing from PMS → after correcting the `problem_active` over-inference, unknown current state stayed `null` and the result was `Clarify` / no priority.

This is a local MVP verification seam. It has no OpenAI API, database, authentication, destructive action, or production deployment.
