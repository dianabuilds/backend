"""content patches table"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20251205_content_patches"
down_revision = "20251204_achievements_workspace_idx"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "content_patches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("data", postgresql.JSON(), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("reverted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["content_id"], ["content_items.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["users.id"], ondelete="SET NULL"
        ),
    )
    op.create_index(
        "ix_content_patches_content_id",
        "content_patches",
        ["content_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_content_patches_content_id", table_name="content_patches")
    op.drop_table("content_patches")
