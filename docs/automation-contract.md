# Automation contract

The rule engine receives structured ticket facts. Unknown facts remain unknown; the system does not invent them.

The fact fields are `affected_properties`, `issue_type`, `affected_bookings`, `other_bookings_working`, `overbooking_risk`, `error_code`, `problem_active`, `next_checkin_hours`, and `claimed_urgency`. Supported normalized issue types are `availability_sync`, `reservation_sync`, and `suspected_duplicate_booking`.

`claimed_urgency` is a separate customer statement. It does not determine the actual priority by itself.

In this MVP, `overbooking_risk=true` may represent a risk explicitly reported by the customer; it is not proof that an external system independently verified the risk.

Current possible routing results are:

- `Incident`
- `L1`
- `L2`
- `Clarify`
- `Unmatched`

When key facts are missing, the engine returns `Clarify` with no priority.

`Unmatched` means the supplied facts are valid and sufficiently present, but none of the currently implemented rules match. The current fallback assigns `Normal`; this is not the same as missing facts and should not be presented as a broadly validated business policy.

Every result also includes `human_review_required`. It is a safety-gate signal, not an approval workflow or an external action.
