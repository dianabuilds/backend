Cutover Plan (MVP DDD → replace legacy)

Scope
- Include: Auth/IAM, Notifications, Profile (username), Search, Flags, Audit.
- Exclude (flagged off or kept experimental): nodes, quests, navigation, ai, moderation, achievements, worlds.

Pre‑checks (Go/No‑Go Gates)
- CI green: ruff, mypy, import‑linter, tests (domain + HTTP).
- Data: `make migrate-ddl` applied; Postgres and Redis healthy.
- Contracts: OpenAPI/JSON Schema present for critical API/events; contract tests pass.
- Observability: 5xx/latency dashboards; events worker errors + DLQ alerts.

Rollout
1) Shadow traffic at 10% (read‑only paths), compare error rates and latency.
2) Canary at 5–10% for write paths (admin notifications, profile rename) with fast rollback switch.
3) Ramp to 50%, then 100% if stable ≥1h.

Rollback
- Switch route at the gateway to legacy; preserve read models; events worker can be paused.

Owner Matrix
- Platform: IAM/Users/Notifications/Search/Audit — team platform.
- Product: Profile/Tags — team product.

Post‑cutover
- Legacy read‑only 24h, archive data, then remove.

