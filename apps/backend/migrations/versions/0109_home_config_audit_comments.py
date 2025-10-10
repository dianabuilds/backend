"""Add comment column to home_config_audits.

Revision ID: 0109_home_config_audit_comments
Revises: 0108_home_config_tables
Create Date: 2025-10-10
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0109_home_config_audit_comments"
down_revision = "0108_home_config_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "home_config_audits",
        sa.Column("comment", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("home_config_audits", "comment")
