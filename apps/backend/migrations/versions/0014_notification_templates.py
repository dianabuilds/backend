"""placeholder for removed notification campaign template adjustments

Revision ID: 0014
Revises: 0013
Create Date: 2025-09-20
"""

from __future__ import annotations

from alembic import op

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Legacy migration removed; retained to keep Alembic history consistent.
    op.execute("SELECT 1")


def downgrade() -> None:
    raise RuntimeError("Downgrading past 0014 is not supported")
