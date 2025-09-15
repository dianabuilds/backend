Schemas Matrix (DDD)

Legend: [x] present, [ ] missing

- platform/events: [x] SQL (outbox), [x] JSON Schemas (events)
- platform/notifications: [x] SQL (campaigns, notifications), [x] OpenAPI, [x] tests
- platform/users: [x] SQL (users)
- platform/iam: [x] JWT/guards, [ ] SQL (nonce/verification optional)
- platform/search: [ ] SQL (in‑memory), [ ] persistence optional (file), [x] tests
- platform/telemetry: [ ] SQL, [x] Redis RUM (optional)
- platform/flags: [ ] SQL, [x] API
- platform/audit: [x] SQL
- platform/billing: [ ] SQL (adapters), [x] API skeleton
- product/profile: [x] via platform.users, [x] API, [x] events
- product/tags: [x] SQL (tag tables, counters), [x] API/admin, [x] tests
- product/nodes: [ ] SQL (in‑memory), [x] API
- product/quests: [ ] SQL (in‑memory), [x] API
- product/navigation: [ ] SQL (depends on nodes), [x] API
- product/ai: [ ] SQL (N/A), [x] API
- product/moderation: [ ] SQL (in‑memory), [x] API
- product/achievements: [ ] SQL (in‑memory), [x] API
- product/worlds: [ ] SQL (in‑memory), [x] API

Notes:
- Profile is persisted through platform.users (users.username, users.bio).
- Tags counters expected in product_tag_usage_counters; writer to be implemented via events.

