"""add workspace_id to outbox and indexes"""
"""add workspace_id to outbox and indexes"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision = "20251211_add_workspace_id_outbox"
down_revision = "20251210_add_workspace_id_user_event_counters"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    table = "outbox"
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
                    "UPDATE outbox SET workspace_id = (SELECT id FROM workspaces WHERE slug='main' LIMIT 1)"
                )
            )
            op.alter_column(table, "workspace_id", nullable=False)
            op.create_index(
                "ix_outbox_workspace_id", table, ["workspace_id"],
            )

    table = "notifications"
    if table in inspector.get_table_names():
        indexes = {idx["name"] for idx in inspector.get_indexes(table)}
        if "ix_notifications_workspace_id" not in indexes:
            op.create_index(
                "ix_notifications_workspace_id",
                table,
                ["workspace_id"],
            )

    table = "media_assets"
    if table in inspector.get_table_names():
        indexes = {idx["name"] for idx in inspector.get_indexes(table)}
        if "ix_media_assets_workspace" in indexes:
            op.drop_index("ix_media_assets_workspace", table_name=table)
        if "ix_media_assets_workspace_id" not in indexes:
            op.create_index(
                "ix_media_assets_workspace_id",
                table,
                ["workspace_id"],
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    table = "outbox"
    if table in inspector.get_table_names():
        indexes = {idx["name"] for idx in inspector.get_indexes(table)}
        if "ix_outbox_workspace_id" in indexes:
            op.drop_index("ix_outbox_workspace_id", table_name=table)
        fks = inspector.get_foreign_keys(table)
        for fk in fks:
            if "workspace_id" in fk["constrained_columns"]:
                op.drop_constraint(fk["name"], table_name=table, type_="foreignkey")
        cols = {c["name"] for c in inspector.get_columns(table)}
        if "workspace_id" in cols:
            op.drop_column(table, "workspace_id")

    table = "notifications"
    if table in inspector.get_table_names():
        indexes = {idx["name"] for idx in inspector.get_indexes(table)}
        if "ix_notifications_workspace_id" in indexes:
            op.drop_index("ix_notifications_workspace_id", table_name=table)

    table = "media_assets"
    if table in inspector.get_table_names():
        indexes = {idx["name"] for idx in inspector.get_indexes(table)}
        if "ix_media_assets_workspace_id" in indexes:
            op.drop_index("ix_media_assets_workspace_id", table_name=table)
        if "ix_media_assets_workspace" not in indexes:
            op.create_index(
                "ix_media_assets_workspace", table, ["workspace_id"],
            )
