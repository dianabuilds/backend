# Tags (Product) вЂ” AGENT Guide

Purpose
- Manage tag catalog (slugs, aliases, blacklist) and expose usage counters for UI.
- Be content-agnostic: tags themselves have no content type; projection carries it.

Scope
- Public API: `/v1/tags?type=all|node|quest&q=&popular=&limit=&offset=`
- Admin API: `/v1/admin/tags/*` (list, aliases CRUD, blacklist, merge, create/delete)
- Events consumed: `node.tags.updated.v1`, `quest.tags.updated.v1` (via outbox consumer)

Storage
- Catalog: monolith tables `tags`, `tag_aliases`, `tag_blacklist` (compat).
- Projection: `tag_usage_counters(author_id, content_type, slug, count, updated_at)`.

Feature Flags
- `FF_TAGS_V1_ENABLED` (bool, default True) вЂ” router and wiring.

Cutover Model
- Read usage from projection only (no JOINs with nodes).
- Update projection from events (consumer) and from backfill.

How to run
- Migrations: `alembic -c alembic.ini upgrade head` (includes `tag_usage_counters` and `content_type`).
- Backfill: `python apps/backend/scripts/backfill_tag_usage_counters.py [--dry-run]`.
- Consumer: `python -m app.workers.tag_usage_projection_consumer` (handles node+quest).

Contracts
- Event payloads:
  - node.tags.updated.v1: `{id, author_id, tags, added, removed, content_type:"node", actor_id}`
  - quest.tags.updated.v1: `{id, author_id, added, removed, content_type:"quest", actor_id?}`
- Admin merge supports `type` in body: `all|node|quest`.

Tests
- Add integration that updates node/quest tags and asserts projection + `/v1/tags`.

Do/DonвЂ™t
- Do keep tag catalog neutral; split by `content_type` only in projection.
- DonвЂ™t add FKs from tags to content tables.

