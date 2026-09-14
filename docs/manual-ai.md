# Manual AI Test Harness

The harness is a manual fallback and learning tool for testing the boundary between AI extraction/normalization and deterministic routing.

Flow:

```text
client text → copied prompt → manual ChatGPT → facts JSON → POST /route → rule_engine.py → decision
```

ChatGPT is used manually to extract and normalize explicit meaning into the automation contract. The page asks it to use `null` for unknown facts and never choose `route` or `priority`. The deterministic `rule_engine.py` makes the business decision.

Manual copy/paste remains available when the automated OpenAI path is not used. It does not call the OpenAI API or spend OpenAI credits itself; after facts are pasted, it does call the local `/route` endpoint.

During testing, the message `Одна бронь Booking не появилась в PMS.` exposed an extraction defect: `problem_active` was incorrectly set to `true` even though the message did not say the problem was still active. The prompt now requires `true` only for an explicitly ongoing problem, `false` only for an explicitly resolved problem, and `null` when the current state is unknown. The corrected facts route to `Clarify` with no priority.
