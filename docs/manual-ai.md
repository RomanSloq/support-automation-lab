# Manual AI Test Harness

The harness is a small local learning tool for testing the boundary between AI extraction and deterministic routing.

Flow:

```text
client text → copied prompt → manual ChatGPT → facts JSON → POST /route → rule_engine.py → decision
```

ChatGPT is used manually as an extractor only. The page asks it to return explicit ticket facts, use `null` for unknown facts, and never choose `route` or `priority`. The deterministic `rule_engine.py` makes the business decision.

Manual copy/paste is used instead of OpenAI API calls so this milestone has no API key, SDK, paid call, or automatic AI integration. In a future step, this manual seam could be replaced by an AI API without changing the role of `rule_engine.py`.

During testing, the message `Одна бронь Booking не появилась в PMS.` exposed an extraction defect: `problem_active` was incorrectly set to `true` even though the message did not say the problem was still active. The prompt now requires `true` only for an explicitly ongoing problem, `false` only for an explicitly resolved problem, and `null` when the current state is unknown. The corrected facts route to `Clarify` with no priority.
