"""add last_login_at column to users

Revision ID: 20251220_add_last_login_at_to_users
Revises: 20251219_drop_quest_data_from_content_items
Create Date: 2025-12-20

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251220_add_last_login_at_to_users"
down_revision = "20251219_drop_quest_data_from_content_items"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "last_login_at")
