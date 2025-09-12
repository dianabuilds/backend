"""Drop legacy workspace_id columns after tenant_id migration

Revision ID: 20250911_drop_workspace_id_columns
Revises: 20250911_add_tenant_id_columns
Create Date: 2025-09-11
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20250911_drop_workspace_id_columns"
down_revision = "20250911_add_tenant_id_columns"
branch_labels = None
depends_on = None


TABLES = [
    "quests",
    "quest_purchases",
    "quest_progress",
    "event_quests",
    "event_quest_completions",
    "audit_logs",
    "outbox",
]


def _drop_column_if_exists(table: str, column: str) -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns(table)}
    if column in cols:
        try:
            op.drop_column(table, column)
        except Exception:
            pass


def upgrade() -> None:
    for table in TABLES:
        _drop_column_if_exists(table, "workspace_id")


def downgrade() -> None:  # pragma: no cover
    raise NotImplementedError

