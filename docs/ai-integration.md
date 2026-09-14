# OpenAI extraction and routing

`POST /ai/route` accepts raw ticket text. The OpenAI extractor normalizes explicit meaning into the existing ticket-facts contract, and the deterministic rule engine makes the business decision.

```text
raw text → OpenAI Responses API → strict Structured Outputs → facts
→ rule_engine.py → route / priority / human_review_required
```

The default model is `gpt-5.6-luna`; `OPENAI_MODEL` can override it. The official Python SDK uses the Responses API with `store=false`, `reasoning.effort=none`, no tools, and a strict JSON Schema that rejects extra fields. `OPENAI_API_KEY` is read only from the environment.

AI performs fact extraction and normalization, not routing. Unknown facts stay `null`. `problem_active` is set only from explicit current/resolved meaning, and claimed urgency never becomes priority by itself.

The extractor must not choose a closest matching issue type. In particular, `availability_sync` requires explicit availability/inventory/free-room synchronization between systems or channels; access to or viewing of a rate plan stays `null` unless another supported category clearly applies. Explicit check-in "now", "right now", or "immediately" becomes `next_checkin_hours = 0`; "today" alone remains `null`.

Successful `/ai/route` responses also include top-level `usage` diagnostics, separate from facts and the business decision. For `gpt-5.6-luna`, `estimated_cost_usd` uses the standard-rate 2026-09-15 estimate: $0.20/M uncached input, $0.02/M cached input, $0.25/M cache-write input, and $1.20/M output. It is an estimate rather than an invoice; an overridden model without a configured price returns `null` instead of a guessed cost. The estimator is intended for short support-ticket requests and does not model special service tiers or the model's long-context surcharge above 272K input tokens.

Technical failures remain technical HTTP errors: empty text, missing credentials, authentication, quota/rate limit, network/API failure, refusal, incomplete output, and invalid model output never become `Clarify` or another business decision.

The ordinary test suite mocks the OpenAI boundary and spends no credits. Live extractor evaluation is opt-in:

```powershell
.\.venv\Scripts\python.exe scripts\eval_ai_extractor.py
```

## Live evaluation evidence

The first real six-case run passed 4/6 and exposed two prompt defects: a generic rate-plan viewing issue was incorrectly normalized to `availability_sync`, and explicit immediate check-in did not become `next_checkin_hours = 0`. After the narrow prompt refinements, the repeated real GPT-5.6 Luna evaluation passed 6/6.

Measured second-run usage was 2,741 input tokens, 396 output tokens, and 3,137 total tokens. `estimated_cost_usd` was $0.0010234 total, or about $0.0001706 per case. This is evidence for these six short requests only; it is neither a statistically meaningful accuracy result nor a production cost forecast.
