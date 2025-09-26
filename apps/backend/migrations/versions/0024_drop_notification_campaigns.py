"""drop notification campaigns legacy table

Revision ID: 0024
Revises: 0023
Create Date: 2025-09-26
"""

from __future__ import annotations

from alembic import op

revision: str = "0024"
down_revision: str | None = "0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS notification_campaigns CASCADE")


def downgrade() -> None:
    raise RuntimeError("Recreating notification_campaigns is not supported")
