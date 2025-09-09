"""Rename workspace_* fields to tenant_* and drop legacy account_id

Revision ID: 20250921_workspace_to_tenant
Revises: 20250913_squashed_initial
Create Date: 2025-09-21

This migration performs a coordinated rename of columns named
"workspace_*" to "tenant_*" across multiple tables to match
application terminology, and removes legacy account_id columns
that no longer exist in the SQLAlchemy models.

Notes:
- Foreign keys and indexes are automatically updated by PostgreSQL
  when columns are renamed; object names (index/constraint names)
  are not changed.
- The migration uses runtime inspection so it can run safely on
  databases that are already partially migrated.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20250921_workspace_to_tenant"
down_revision = "20250913_squashed_initial"
branch_labels = None
depends_on = None


def _has_column(conn: sa.Connection, table: str, column: str, schema: str | None = None) -> bool:
    '''Check column existence via information_schema to avoid reflection warnings.'''
    schema = schema or conn.dialect.default_schema_name or 'public'
    sql = sa.text(
        'select 1 from information_schema.columns '
        'where table_schema = :schema and table_name = :table and column_name = :column limit 1'
    )
    res = conn.execute(sql, {'schema': schema, 'table': table, 'column': column}).first()
    return res is not None


def _rename_column_if_exists(conn: sa.Connection, table: str, old: str, new: str) -> None:
    if _has_column(conn, table, old) and not _has_column(conn, table, new):
        op.alter_column(table, old, new_column_name=new)


def _drop_column_if_exists(conn: sa.Connection, table: str, column: str) -> None:
    if _has_column(conn, table, column):
        op.drop_column(table, column)


def upgrade() -> None:
    bind = op.get_bind()

    # 1) Rename workspace_id -> tenant_id for tenant-scoped tables
    for table in (
        "quests",
        "quest_purchases",
        "quest_progress",
        "event_quests",
        "event_quest_completions",
        "audit_logs",
        "outbox",
    ):
        _rename_column_if_exists(bind, table, 'workspace_id', 'tenant_id')

    # 2) Rename default_workspace_id -> default_tenant_id on users
    _rename_column_if_exists(bind, 'users', 'default_workspace_id', 'default_tenant_id')

    # 3) Drop legacy account_id on nodes if present (removed from schema)
    _drop_column_if_exists(bind, 'nodes', 'account_id')


def downgrade() -> None:  # pragma: no cover
    # Reversible renames (best effort); account_id recreation is not supported.
    bind = op.get_bind()

    for table in (
        "quests",
        "quest_purchases",
        "quest_progress",
        "event_quests",
        "event_quest_completions",
        "audit_logs",
        "outbox",
    ):
        _rename_column_if_exists(bind, table, 'tenant_id', 'workspace_id')

    _rename_column_if_exists(bind, 'users', 'default_tenant_id', 'default_workspace_id')

    # Do NOT re-add nodes.account_id since original type/constraints may vary.
    # If a downgrade is required, add the column back manually as needed.
    raise NotImplementedError('Automatic downgrade of account_id is not supported')
