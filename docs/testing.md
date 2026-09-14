# Testing

## Automated suite

The current automated test suite includes HTTP E2E checks, negative request validation, and mocked OpenAI integration. It also verifies prompt boundaries for unsupported rate-plan text, immediate check-in normalization, usage mapping, and a synthetic Luna cost estimate.

| Scenario | Expected result | Actual result |
| --- | --- | --- |
| Mass availability issue | `Incident` / `Critical` | PASS |
| One local reservation issue | `L1` / `Normal` | PASS |
| Missing facts with `claimed_urgency = "high"` | `Clarify` / no priority | PASS |
| Active reservation sync with error `401` | `L2` / `High` | PASS |
| Safe case review flag | `human_review_required = false` | PASS |
| Suspected duplicate review flag | `L2` / `High` / `true` | PASS |

Full test run: **23/23 PASS, 0 errors**. This confirms the encoded cases only; it is not a claim of 100% real-world accuracy. The ordinary suite makes no paid OpenAI calls.

## Live model evaluation

The first real GPT-5.6 Luna evaluation passed 4/6 and revealed two extraction boundaries: closest-match classification of an unsupported rate-plan issue and missing zero-hour normalization for immediate check-in. After prompt refinement, the repeated evaluation passed **6/6**.

Measured repeated-run usage: 2,741 input tokens, 396 output tokens, 3,137 total tokens, and $0.0010234 estimated total cost (about $0.0001706 per case). Six cases are a small regression set, not statistically meaningful accuracy or a production cost forecast.

## Manual verification

Postman independently verified two real `/ai/route` flows with HTTP `200`: mass availability → `Incident` / `Critical`, and one missing Booking reservation with unknown current state → `Clarify` / no priority. Earlier structured `/route`, webhook, and manual-harness checks remain separate evidence.
