# AGENT — Achievements

Structure: api/, application/, domain/, adapters/.

Rules
- Keep domain logic in application/ and domain/ (no I/O).
- Adapters provide storage (here: in-memory) and must not import the monolith.
- API uses FastAPI and resolves services via `get_container(req)`.

API
- User: GET /v1/achievements
- Admin: CRUD + grant/revoke under /v1/admin/achievements

