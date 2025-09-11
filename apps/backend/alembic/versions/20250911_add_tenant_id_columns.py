"""Add tenant_id columns alongside workspace_id and backfill

Revision ID: 20250911_add_tenant_id_columns
Revises: 20251021_shared_objects_profile_id
Create Date: 2025-09-11
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20250911_add_tenant_id_columns"
down_revision = "20251021_shared_objects_profile_id"
branch_labels = None
depends_on = None


TABLES = [
    # table, has_fk_to_workspaces
    ("quests", True),
    ("quest_purchases", True),
    ("quest_progress", True),
    ("event_quests", True),
    ("event_quest_completions", True),
    ("audit_logs", False),
    ("outbox", False),
]


def _add_column_if_missing(table: str) -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns(table)}
    if "tenant_id" not in cols:
        # Postgres-friendly type; for other dialects this will be created as a generic type
        try:
            op.add_column(table, sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
        except Exception:
            # Fallback to generic String if dialect lacks UUID
            op.add_column(table, sa.Column("tenant_id", sa.String(length=36), nullable=True))


def _copy_data(table: str) -> None:
    # Best-effort: copy workspace_id -> tenant_id where present
    try:
        op.execute(
            sa.text(
                f"UPDATE {table} SET tenant_id = workspace_id WHERE tenant_id IS NULL AND workspace_id IS NOT NULL"
            )
        )
    except Exception:
        pass


def _add_index_if_missing(table: str) -> None:
    idx_name = f"ix_{table}_tenant_id"
    bind = op.get_bind()
    insp = sa.inspect(bind)
    try:
        existing = {i.get("name") for i in insp.get_indexes(table)}
    except Exception:
        existing = set()
    if idx_name not in existing:
        try:
            op.create_index(idx_name, table, ["tenant_id"], unique=False)
        except Exception:
            pass


def _add_fk_if_possible(table: str) -> None:
    # Add FK to workspaces.id when table had FK on workspace_id previously
    fk_name = f"fk_{table}_tenant_id_workspaces"
    try:
        op.create_foreign_key(
            fk_name,
            source_table=table,
            referent_table="workspaces",
            local_cols=["tenant_id"],
            remote_cols=["id"],
            ondelete=None,
        )
    except Exception:
        # Dialect may not support constraints (e.g., SQLite) or FK may already exist
        pass


def upgrade() -> None:
    for table, has_fk in TABLES:
        _add_column_if_missing(table)
        _copy_data(table)
        _add_index_if_missing(table)
        if has_fk:
            _add_fk_if_possible(table)


def downgrade() -> None:  # pragma: no cover
    raise NotImplementedError

