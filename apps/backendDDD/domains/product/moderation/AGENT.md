# AGENT — Moderation

Structure: api/, application/, adapters/.

Rules
- Async ports; in-memory adapter provided for dev.
- No imports from monolith.

API
- /v1/moderation/cases* (list/create)
- /v1/moderation/cases/{id}/notes (add note)

