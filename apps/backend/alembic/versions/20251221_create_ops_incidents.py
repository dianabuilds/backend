"""create ops_incidents table

Revision ID: 20251221_create_ops_incidents
Revises: 20251220_add_last_login_at_to_users
Create Date: 2025-12-21

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251221_create_ops_incidents"
down_revision = "20251220_add_last_login_at_to_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ops_incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("message", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_ops_incidents_created_at", "ops_incidents", ["created_at"], if_not_exists=True
    )


def downgrade() -> None:
    op.drop_index(
        "ix_ops_incidents_created_at", table_name="ops_incidents", if_exists=True
    )
    op.drop_table("ops_incidents")
