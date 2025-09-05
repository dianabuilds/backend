from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "20241002_shared_objects"
down_revision = "20240920_account_id_bigserial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shared_objects",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("object_type", sa.String(), nullable=False),
        sa.Column("object_id", UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", UUID(as_uuid=True), nullable=False),
        sa.Column("permissions", sa.String(), nullable=False),
        sa.UniqueConstraint("object_type", "object_id", "account_id", name="uq_shared_object"),
    )
    op.create_index("ix_shared_objects_account_id", "shared_objects", ["account_id"])


def downgrade() -> None:
    op.drop_table("shared_objects")
