Tags Domain (Product)

Scope
- Endpoints: public list for current user (/v1/tags) and admin tools (/v1/admin/tags).
- Operations: tag listing with usage counters, aliases CRUD, blacklist, merge, create/delete tag.

Storage Strategy (Phase 1 → 2)
- Phase 1: uses existing monolith tables (tags, tag_aliases, tag_blacklist, node_tags, content_tags) via sync SQLAlchemy.
- Phase 2: introduces projection table `tag_usage_counters` (author_id, slug, count) updated by Nodes events; public listing reads from the projection only (no joins with nodes).

Cutover Plan
1) Public list + admin tools run via DDD service. Public list reads projection only.
2) Nodes emit `node.tags.updated.v1` and synchronously apply usage diffs; later switch to async bus subscriber.
3) Once Nodes/Content are migrated to dedicated schema, move projection accordingly; run backfill for counters; drop legacy joins.

Notes
- Admin operations are guarded via DDD IAM require_admin.
- Search indexing and event publishing can be added when search/events wiring is enabled for tags.

Admin Listing
- Query supports `type=node|quest|all` (default: `all`).
- For `node` or `quest` the usage counters are filtered by `content_type`.
- For `all` the counters are summed across content types.
