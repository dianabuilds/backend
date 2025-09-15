# AGENT — Nodes

Structure: api/, application/, domain/, adapters/.

Rules
- NodeService uses ports: Repo, TagCatalog, Outbox, UsageProjection.
- In-memory adapters provided; no monolith imports allowed.

API
- /v1/nodes/{id}
- /v1/nodes/{id}/tags

