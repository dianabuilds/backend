# Performance Playbook

## Async Pipelines
- Profiling artefacts: `var/profiling/nodes-engagement.svg`, `var/profiling/notifications-worker.svg`, textual summary `nodes-engagement.log`.
- Flamegraphs capture `domains.product.nodes` engagement path and notification broadcast worker baseline (single-batch smoke tests).
- Profiling rerun command (local):
  ```bash
  python -m flameprof -o var/profiling/nodes-engagement.svg -m pytest -- tests/unit/nodes/test_use_cases.py::TestEngagementService::test_register_view_success -q
  python -m flameprof -o var/profiling/notifications-worker.svg -m pytest -- apps/backend/domains/platform/notifications/tests/test_broadcast_worker.py::test_broadcast_worker_updates_metrics -q
  ```

## Node Cache
- `RedisNodeCache` enabled by default (fallback to in-memory in tests). TTL 300s, cap 5000 entries; override via env:
  - `APP_NODES_CACHE_TTL` (seconds)
  - `APP_NODES_CACHE_MAX_ENTRIES`
- Cached keys: `nodes:v1:id:<id>`, `nodes:v1:slug:<slug>`; invalidated on create/update/tags/delete/embedding refresh.
- In-memory cache retains same TTL/cap for offline runtimes (evicts oldest on overflow).

## Database Indexes
Applied by migration `0110_nodes_notifications_indexes`:
- `nodes (author_id, id DESC)` � speeds author listing.
- `product_node_tags (node_id, slug)` � supports tag updates + dev-blog filters.
- `notification_receipts (user_id, placement, created_at DESC)` and `(event_id)` � inbox/outbox lookups.
- `moderation_cases` functional indexes on status/type/queue/assignee for admin queries.

## Reprofiling Triggers
- API latency regression >20% on `/v1/nodes` or `/v1/notifications`.
- Cache hit ratio <85% (Redis `INFO keyspace`, see `product:nodes:v1` prefix).
- New filters added to moderation listings or notification placements.
- Embedding worker provider/timeout changes.

## Redis / Postgres Limits
- Redis: ensure cache DB (~5k entries, ~1.5 MB assuming ~300B/item). Watch `maxmemory-policy` (use `allkeys-lru`).
- Postgres: indexes add ~50-100 MB (depending on table size). Run `ANALYZE` after large imports.
- Re-run `scripts/api_benchmark.py` + smoke pytest after schema/data migration; capture results in `var/api-benchmarks.json`.

