# Automation contract

The rule engine receives structured ticket facts. Unknown facts remain unknown; the system does not invent them.

`claimed_urgency` is a separate customer statement. It does not determine the actual priority by itself.

Current possible routing results are:

- `Incident`
- `L1`
- `Clarify`

When key facts are missing, the engine returns `Clarify` with no priority.
