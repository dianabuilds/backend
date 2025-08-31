"""create background_job_history table

Revision ID: 20251222_create_background_job_history
Revises: 20251221_create_ops_incidents
Create Date: 2025-12-22

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251222_create_background_job_history"
down_revision = "20251221_create_ops_incidents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "background_job_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("log_url", sa.String(), nullable=True),
        sa.Column(
            "started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_background_job_history_started_at",
        "background_job_history",
        ["started_at"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_background_job_history_started_at",
        table_name="background_job_history",
        if_exists=True,
    )
    op.drop_table("background_job_history")
