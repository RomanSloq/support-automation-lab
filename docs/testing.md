# Testing

The current automated test set contains three scenarios:

| Scenario | Expected result | Actual result |
| --- | --- | --- |
| Mass availability issue | `Incident` / `Critical` | PASS |
| One local reservation issue | `L1` / `Normal` | PASS |
| Missing facts with `claimed_urgency = "high"` | `Clarify` / no priority | PASS |

Full test run: **3/3 PASS, 0 errors**.
