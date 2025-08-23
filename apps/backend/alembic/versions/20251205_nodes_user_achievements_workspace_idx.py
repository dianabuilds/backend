"""add workspace indexes for nodes and user achievements"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision = "20251205_nodes_user_achievements_workspace_idx"
down_revision = "20251204_achievements_workspace_idx"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # nodes table index
    if "nodes" in inspector.get_table_names():
        indexes = {idx["name"] for idx in inspector.get_indexes("nodes")}
        if "ix_nodes_workspace_id" not in indexes:
            op.create_index("ix_nodes_workspace_id", "nodes", ["workspace_id"])

    # user_achievements table
    if "user_achievements" in inspector.get_table_names():
        cols = {c["name"] for c in inspector.get_columns("user_achievements")}
        if "workspace_id" not in cols:
            op.add_column(
                "user_achievements",
                sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True),
            )
            op.create_foreign_key(
                None, "user_achievements", "workspaces", ["workspace_id"], ["id"]
            )
            op.execute(
                sa.text(
                    "UPDATE user_achievements ua SET workspace_id = a.workspace_id FROM achievements a WHERE ua.achievement_id = a.id"
                )
            )
            op.alter_column("user_achievements", "workspace_id", nullable=False)
        indexes = {idx["name"] for idx in inspector.get_indexes("user_achievements")}
        if "ix_user_achievements_workspace_id" not in indexes:
            op.create_index(
                "ix_user_achievements_workspace_id",
                "user_achievements",
                ["workspace_id"],
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "user_achievements" in inspector.get_table_names():
        indexes = {idx["name"] for idx in inspector.get_indexes("user_achievements")}
        if "ix_user_achievements_workspace_id" in indexes:
            op.drop_index(
                "ix_user_achievements_workspace_id", table_name="user_achievements"
            )
        cols = {c["name"] for c in inspector.get_columns("user_achievements")}
        if "workspace_id" in cols:
            op.drop_column("user_achievements", "workspace_id")

    if "nodes" in inspector.get_table_names():
        indexes = {idx["name"] for idx in inspector.get_indexes("nodes")}
        if "ix_nodes_workspace_id" in indexes:
            op.drop_index("ix_nodes_workspace_id", table_name="nodes")
