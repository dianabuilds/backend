"""create workspaces and workspace_members tables

Revision ID: 20250822_ws_members
Revises: 20250820_pg_types_upgrade, 20250820_move_raw_external
Create Date: 2025-08-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = "20250822_ws_members"
down_revision = ("20250820_pg_types_upgrade", "20250820_move_raw_external")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workspaces",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False, unique=True),
        sa.Column("owner_user_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("settings_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "workspace_members",
        sa.Column("workspace_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("permissions_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_table("workspace_members")
    op.drop_table("workspaces")
