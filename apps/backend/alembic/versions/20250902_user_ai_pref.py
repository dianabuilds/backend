"""create user_ai_pref table

Revision ID: 20250902_user_ai_pref
Revises: 20250901_world_char_ws
Create Date: 2025-09-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision = "20250902_user_ai_pref"
down_revision = "20250901_world_char_ws"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("user_ai_pref"):
        op.create_table(
            "user_ai_pref",
            sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("model", sa.String(), nullable=False),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if inspector.has_table("user_ai_pref"):
        op.drop_table("user_ai_pref")
