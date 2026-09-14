# Testing

The current automated test set contains eight scenarios:

| Scenario | Expected result | Actual result |
| --- | --- | --- |
| Mass availability issue | `Incident` / `Critical` | PASS |
| One local reservation issue | `L1` / `Normal` | PASS |
| Missing facts with `claimed_urgency = "high"` | `Clarify` / no priority | PASS |
| Active reservation sync with error `401` | `L2` / `High` | PASS |
| Safe case review flag | `human_review_required = false` | PASS |
| Suspected duplicate review flag | `L2` / `High` / `true` | PASS |

Full test run: **8/8 PASS, 0 errors**.
