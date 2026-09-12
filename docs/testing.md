# Testing

The current automated test set contains four scenarios:

| Scenario | Expected result | Actual result |
| --- | --- | --- |
| Mass availability issue | `Incident` / `Critical` | PASS |
| One local reservation issue | `L1` / `Normal` | PASS |
| Missing facts with `claimed_urgency = "high"` | `Clarify` / no priority | PASS |
| Active reservation sync with error `401` | `L2` / `High` | PASS |

Full test run: **4/4 PASS, 0 errors**.
