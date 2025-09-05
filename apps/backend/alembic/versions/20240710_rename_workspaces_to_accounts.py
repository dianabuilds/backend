"""rename workspaces to accounts"""

from alembic import op
import sqlalchemy as sa

revision = "20240710_rename_workspaces_to_accounts"
down_revision = "20240620_fix_transition_node_ids"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("workspaces", "accounts")
    op.rename_table("workspace_members", "account_members")
    op.alter_column("account_members", "workspace_id", new_column_name="account_id")
    op.alter_column("nodes", "workspace_id", new_column_name="account_id")


def downgrade() -> None:
    op.alter_column("nodes", "account_id", new_column_name="workspace_id")
    op.alter_column("account_members", "account_id", new_column_name="workspace_id")
    op.rename_table("account_members", "workspace_members")
    op.rename_table("accounts", "workspaces")
