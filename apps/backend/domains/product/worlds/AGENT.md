# AGENT — Worlds

Structure: api/, application/, domain/, adapters/.

Rules
- No monolith imports. Use repo interfaces + adapters (in-memory here).
- Admin-only API under /v1/admin/worlds with tenant_id query.

API
- Worlds: list/create/update/delete
- Characters: list/create/update/delete

