from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision = "20260119_add_workspace_id_to_audit_logs"
down_revision = "20260118_drop_node_tags_node_uuid"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    table = "audit_logs"
    if table in inspector.get_table_names():
        cols = {c["name"] for c in inspector.get_columns(table)}
        if "workspace_id" not in cols:
            op.add_column(
                table,
                sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True),
            )
        fks = {fk["name"] for fk in inspector.get_foreign_keys(table)}
        if "fk_audit_logs_workspace_id" not in fks:
            op.create_foreign_key(
                "fk_audit_logs_workspace_id",
                table,
                "workspaces",
                ["workspace_id"],
                ["id"],
            )
        indexes = {idx["name"] for idx in inspector.get_indexes(table)}
        if "ix_audit_logs_workspace_id" not in indexes:
            op.create_index("ix_audit_logs_workspace_id", table, ["workspace_id"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    table = "audit_logs"
    if table in inspector.get_table_names():
        indexes = {idx["name"] for idx in inspector.get_indexes(table)}
        if "ix_audit_logs_workspace_id" in indexes:
            op.drop_index("ix_audit_logs_workspace_id", table_name=table)

        fks = {fk["name"] for fk in inspector.get_foreign_keys(table)}
        if "fk_audit_logs_workspace_id" in fks:
            op.drop_constraint(
                "fk_audit_logs_workspace_id", table_name=table, type_="foreignkey"
            )

        cols = {c["name"] for c in inspector.get_columns(table)}
        if "workspace_id" in cols:
            op.drop_column(table, "workspace_id")
