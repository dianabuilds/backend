"""add indexes for workspace ownership and membership"""

from alembic import op
import sqlalchemy as sa

revision = "20251207_add_workspace_indexes"
down_revision = "20251206_add_workspace_type_is_system"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_workspaces_owner_user_id", "workspaces", ["owner_user_id"]
    )
    op.create_index(
        "ix_workspaces_created_at", "workspaces", ["created_at"]
    )
    op.create_index(
        "ix_workspace_members_workspace_id_role",
        "workspace_members",
        ["workspace_id", "role"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_workspace_members_workspace_id_role", table_name="workspace_members"
    )
    op.drop_index("ix_workspaces_created_at", table_name="workspaces")
    op.drop_index("ix_workspaces_owner_user_id", table_name="workspaces")
