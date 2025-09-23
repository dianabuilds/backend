"""
Add notification_templates table for reusable notification blueprints and link campaigns.

Revision ID: 0014
Revises: 0013
Create Date: 2025-09-21
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.create_table(
        "notification_templates",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("locale", sa.Text(), nullable=True),
        sa.Column("variables", JSONB, nullable=True),
        sa.Column("meta", JSONB, nullable=True),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_notification_templates_slug",
        "notification_templates",
        ["slug"],
        unique=True,
    )
    op.create_index(
        "ix_notification_templates_locale",
        "notification_templates",
        ["locale"],
    )

    op.add_column(
        "notification_campaigns",
        sa.Column("template_id", UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_notification_campaigns_template",
        "notification_campaigns",
        ["template_id"],
    )
    op.create_foreign_key(
        "fk_notification_campaigns_template",
        "notification_campaigns",
        "notification_templates",
        ["template_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_notification_campaigns_template",
        "notification_campaigns",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_notification_campaigns_template",
        table_name="notification_campaigns",
    )
    op.drop_column("notification_campaigns", "template_id")
    op.drop_index("ix_notification_templates_locale", table_name="notification_templates")
    op.drop_index("ix_notification_templates_slug", table_name="notification_templates")
    op.drop_table("notification_templates")
