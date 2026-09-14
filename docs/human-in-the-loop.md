# Human-in-the-loop safety gate

`Clarify` and human review solve different problems:

- `Clarify` means there are not enough facts for a confident routing decision.
- `human_review_required` means route and priority can be determined, but a potentially risky next action must be checked by a person.

The result includes `human_review_required`:

- `false` — mandatory human review is not required for this decision;
- `true` — a person must review any potentially risky next action.

Safe case: one `reservation_sync` booking while other bookings work → `L1` / `Normal` / `false`.

Risky case: `suspected_duplicate_booking`, two affected bookings, check-in now, active problem, and high claimed urgency → `L2` / `High` / `true`.

The duplicate is suspected, not confirmed. The system does not delete, merge, cancel, or change bookings in external systems. An approval workflow is not implemented; this field is only a safety gate signal.

The current contract has no separate `migration` field, so the system does not claim to check PMS migration status.
