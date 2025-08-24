"""add workspace_id to user_event_counters

Revision ID: 20251210_add_workspace_id_user_event_counters
Revises: 20251209_add_quest_data_to_content_items
Create Date: 2025-12-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20251210_add_workspace_id_user_event_counters"
down_revision = "20251209_add_quest_data_to_content_items"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table = "user_event_counters"

    if table in inspector.get_table_names():
        cols = {c["name"] for c in inspector.get_columns(table)}
        if "workspace_id" not in cols:
            op.add_column(
                table,
                sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True),
            )
            op.create_foreign_key(None, table, "workspaces", ["workspace_id"], ["id"])
            op.execute(
                sa.text(
                    "UPDATE user_event_counters SET workspace_id = (SELECT id FROM workspaces WHERE slug='main' LIMIT 1)"
                )
            )
            op.alter_column(table, "workspace_id", nullable=False)

        pk = inspector.get_pk_constraint(table)
        pk_cols = pk.get("constrained_columns", [])
        if set(pk_cols) != {"workspace_id", "user_id", "event"}:
            op.drop_constraint(pk["name"], table_name=table, type_="primary")
            op.create_primary_key(None, table, ["workspace_id", "user_id", "event"])

        indexes = {idx["name"] for idx in inspector.get_indexes(table)}
        if "ix_user_event_counters_workspace_id" not in indexes:
            op.create_index(
                "ix_user_event_counters_workspace_id",
                table,
                ["workspace_id"],
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    table = "user_event_counters"

    if table in inspector.get_table_names():
        indexes = {idx["name"] for idx in inspector.get_indexes(table)}
        if "ix_user_event_counters_workspace_id" in indexes:
            op.drop_index("ix_user_event_counters_workspace_id", table_name=table)

        pk = inspector.get_pk_constraint(table)
        if set(pk.get("constrained_columns", [])) == {
            "workspace_id",
            "user_id",
            "event",
        }:
            op.drop_constraint(pk["name"], table_name=table, type_="primary")
            op.create_primary_key(None, table, ["user_id", "event"])

        fks = inspector.get_foreign_keys(table)
        for fk in fks:
            if "workspace_id" in fk["constrained_columns"]:
                op.drop_constraint(fk["name"], table_name=table, type_="foreignkey")

        cols = {c["name"] for c in inspector.get_columns(table)}
        if "workspace_id" in cols:
            op.drop_column(table, "workspace_id")
