# Database Migrations

This project uses Alembic for schema migrations.

## Squashed Baseline (2025‑09‑13)

All previous revisions were squashed into a single baseline
`20250913_squashed_initial`. This file creates the current schema directly
from SQLAlchemy models.

- Existing databases already on the old head:
  - Stamp the new baseline without running historical migrations:
    ```bash
    alembic stamp 20250913_squashed_initial
    ```
- New databases / fresh environments:
  - Create schema from scratch:
    ```bash
    alembic upgrade head
    ```

## Creating a new migration

1. Ensure the DB is at head: `alembic upgrade head`.
2. Make your model changes.
3. Generate: `alembic revision --autogenerate -m "<summary>"`.
4. Review and apply: `alembic upgrade head`.

## CI checks

We recommend adding workflow steps to verify migrations:
- `alembic upgrade head` against a disposable database
- `alembic downgrade -1` and back to `head`
- Ensure a single head: `alembic heads` → 1 result

## Tenant ID introduction (2025-09-11)

To unify identifiers across domains, we introduce `tenant_id` alongside legacy
`workspace_id` in several tables and backfill data. See ADR-001 for details.

Affected tables:
- `quests` → add `tenant_id`; later drop `workspace_id`
- `quest_purchases` → add `tenant_id`; later drop `workspace_id`
- `quest_progress` → add `tenant_id`; later drop `workspace_id`
- `event_quests` → add `tenant_id`; later drop `workspace_id`
- `event_quest_completions` → add `tenant_id`; later drop `workspace_id`
- `audit_logs` → add `tenant_id`; later drop `workspace_id`
- `outbox` → add `tenant_id`; later drop `workspace_id`

Operational notes:
- Apply revision `20250911_add_tenant_id_columns` on Postgres first.
- Applications now accept only `tenant_id` in request params and paths. Legacy
  `workspace_id` parameters are not supported.
- Follow-up revision `20250911_drop_workspace_id_columns` removes legacy
  `workspace_id` columns after the codebase fully uses `tenant_id`.
