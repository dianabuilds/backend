# Migration 0106_node_engagement

## Changes
- Columns on `nodes`: `views_count`, `reactions_like_count`, `comments_disabled`, `comments_locked_by`, `comments_locked_at`.
- Table `node_views_daily` for daily view aggregation.
- Table `node_reactions` with unique `(node_id, user_id, reaction_type)` constraint.
- Table `node_comments` with tree hierarchy (depth <= 5), status check, indexes on `node_id`, `parent_comment_id`, `author_id`.
- Table `node_comment_bans` for local bans.
- Analytics indexes: `ix_nodes_views_count`, `ix_nodes_reactions_like_count`, `ix_nodes_comments_disabled` plus indexes on new tables.

## Pre-flight
1. Ensure `pgcrypto` is enabled (UUID casting) and `pgvector` registered if used elsewhere.
2. Check free space: node engagement tables can grow quickly.
3. Take backups (snapshot or `pg_dump`) before upgrading production.

## Apply
```bash
poetry run alembic upgrade head
```

Rollback (if needed):
```bash
poetry run alembic downgrade 0105_moderator_user_notes
```

## Post-checks
- `SELECT column_name FROM information_schema.columns WHERE table_name = 'nodes' AND column_name IN ('views_count','reactions_like_count','comments_disabled');`
- `SELECT count(*) FROM node_comments;` to confirm table presence.
- `\d+ node_reactions` in psql to verify indexes.

## Operational Notes
- No backfill: counters start at zero. Prepare a one-off import script if historical data must be restored.
- View rate limiting relies on Redis configuration in `apps/backend/app/api_gateway/wires.py` (per-day TTL).

\n## Status\n- 2025-10-03: migration applied and smoke checks passed.
