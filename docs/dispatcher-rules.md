# Dispatcher rules

These are the only rules implemented at the current milestone:

1. At least 2 affected properties, `availability_sync`, and overbooking risk → `Incident` / `Critical`.
2. Exactly 1 affected property, `reservation_sync`, 1 affected booking, and other bookings working → `L1` / `Normal`.
3. Missing key facts → `Clarify` / priority not assigned.
4. Active `reservation_sync` with error code `401` → `L2` / `High`.
5. Active `suspected_duplicate_booking` affecting bookings with check-in now → `L2` / `High` / human review required.

The two technical/safety-sensitive L2 rules are evaluated before the missing-facts fallback. Valid facts that match none of these rules return the current default `Unmatched` / `Normal`; this default has not been validated as a general routing policy.

The current duplicate condition requires `affected_bookings` to be known, but does not enforce a minimum of two. Only the tested two-booking scenario is confirmed; changing that threshold requires a separate business decision.

Other support scenarios are planned, but are not implemented yet.
