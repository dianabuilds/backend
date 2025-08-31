"""add workspace type and is_system columns"""

from alembic import op
import sqlalchemy as sa

revision = "20251206_add_workspace_type_is_system"
down_revision = "20251205_nodes_user_achievements_workspace_idx"
branch_labels = None
depends_on = None

workspace_type = sa.Enum("personal", "team", "global", name="workspace_type")


def upgrade() -> None:
    # Create enum type
    workspace_type.create(op.get_bind(), checkfirst=True)
    # Add columns with default values
    op.add_column(
        "workspaces",
        sa.Column("type", workspace_type, nullable=False, server_default="team"),
    )
    op.add_column(
        "workspaces",
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    # Backfill existing rows (explicit for clarity)
    op.execute("UPDATE workspaces SET type='team' WHERE type IS NULL")
    op.execute("UPDATE workspaces SET is_system=false WHERE is_system IS NULL")


def downgrade() -> None:
    op.drop_column("workspaces", "is_system")
    op.drop_column("workspaces", "type")
    workspace_type.drop(op.get_bind(), checkfirst=True)
