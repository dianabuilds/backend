"""add workspace role enum and content visibility

Revision ID: 20251101_ws_role_visibility
Revises: 20251010_add_media_assets_table
Create Date: 2025-11-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251101_ws_role_visibility"
down_revision = "20251010_add_media_assets_table"
branch_labels = None
depends_on = None

workspace_role = postgresql.ENUM(
    "owner", "editor", "viewer", name="workspace_role"
)
content_status = postgresql.ENUM(
    "draft", "in_review", "published", "archived", name="content_status", create_type=False
)
content_visibility = postgresql.ENUM(
    "private", "unlisted", "public", name="content_visibility", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    workspace_role.create(bind, checkfirst=True)
    content_status.create(bind, checkfirst=True)

    op.execute(
        "UPDATE workspace_members SET role = 'viewer' "
        "WHERE role NOT IN ('owner', 'editor', 'viewer')"
    )
    op.alter_column(
        "workspace_members",
        "role",
        existing_type=sa.String(),
        type_=workspace_role,
        postgresql_using="role::text::workspace_role",
        existing_nullable=False,
    )

    content_visibility.create(bind, checkfirst=True)
    op.add_column(
        "content_items",
        sa.Column(
            "visibility", content_visibility, nullable=False, server_default="private"
        ),
    )


def downgrade() -> None:
    op.drop_column("content_items", "visibility")

    op.alter_column(
        "workspace_members",
        "role",
        existing_type=workspace_role,
        type_=sa.String(),
        postgresql_using="role::text",
        existing_nullable=False,
    )
    workspace_role.drop(op.get_bind(), checkfirst=True)
