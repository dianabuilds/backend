# AGENT — Quests

Structure: api/, application/, domain/, adapters/.

Rules
- Use ports (Repo, TagCatalog, Outbox); in-memory adapters provided.
- No monolith imports.

API
- /v1/quests (create)
- /v1/quests/{id} (get)
- /v1/quests/{id}/tags (update)

