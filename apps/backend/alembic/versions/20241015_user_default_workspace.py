from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "20241015_user_default_workspace"
down_revision = "20241002_shared_objects"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("default_workspace_id", UUID(as_uuid=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "default_workspace_id")
