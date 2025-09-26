"""add explicit content columns to notifications

Revision ID: 0022
Revises: 0021
Create Date: 2025-09-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0022"
down_revision: str | None = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "notifications",
        sa.Column("title", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "notifications",
        sa.Column("message", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "notifications",
        sa.Column("placement", sa.Text(), nullable=False, server_default="inbox"),
    )
    op.add_column(
        "notifications",
        sa.Column("is_preview", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    op.execute(
        sa.text(
            """
            UPDATE notifications
            SET
                title = COALESCE(payload->>'title', title),
                message = COALESCE(payload->>'message', message),
                placement = COALESCE(payload->>'placement', placement),
                is_preview = COALESCE((payload->>'is_preview')::boolean, is_preview)
            """
        )
    )

    op.alter_column("notifications", "title", server_default=None)
    op.alter_column("notifications", "message", server_default=None)
    op.alter_column("notifications", "placement", server_default=None)
    op.alter_column("notifications", "is_preview", server_default=None)


def downgrade() -> None:
    op.drop_column("notifications", "is_preview")
    op.drop_column("notifications", "placement")
    op.drop_column("notifications", "message")
    op.drop_column("notifications", "title")
