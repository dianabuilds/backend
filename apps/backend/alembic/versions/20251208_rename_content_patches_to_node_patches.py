"""rename content_patches to node_patches"""

from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20251208_rename_content_patches_to_node_patches"
# Merge together migrations that added "content_patches" and subsequent index changes.
down_revision = (
    "20251207_add_workspace_indexes",
    "20251205_content_patches",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("content_patches", "node_patches")
    op.alter_column(
        "node_patches",
        "content_id",
        new_column_name="node_id",
        existing_type=postgresql.UUID(as_uuid=True),
        existing_nullable=False,
    )
    op.execute(
        "ALTER INDEX ix_content_patches_content_id RENAME TO ix_node_patches_node_id"
    )


def downgrade() -> None:
    op.execute(
        "ALTER INDEX ix_node_patches_node_id RENAME TO ix_content_patches_content_id"
    )
    op.alter_column(
        "node_patches",
        "node_id",
        new_column_name="content_id",
        existing_type=postgresql.UUID(as_uuid=True),
        existing_nullable=False,
    )
    op.rename_table("node_patches", "content_patches")
