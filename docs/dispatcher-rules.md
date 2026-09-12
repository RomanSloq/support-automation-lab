# Dispatcher rules

These are the only rules implemented at the current milestone:

1. At least 2 affected properties, `availability_sync`, and overbooking risk → `Incident` / `Critical`.
2. Exactly 1 affected property, `reservation_sync`, 1 affected booking, and other bookings working → `L1` / `Normal`.
3. Missing key facts → `Clarify` / priority not assigned.

Other support scenarios are planned, but are not implemented yet.
