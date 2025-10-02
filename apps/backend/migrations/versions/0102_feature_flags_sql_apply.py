"""Ensure feature flag tables exist (repeatable safety net).

Revision ID: 0102_feature_flags_sql_apply
Revises: 0101_feature_flags_sql
Create Date: 2025-10-01
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision = "0102_feature_flags_sql_apply"
down_revision = "0101_feature_flags_sql"
branch_labels = None
depends_on = None


def _ensure_enum(bind, enum: pg.ENUM) -> None:
    enum.create(bind, checkfirst=True)


def _ensure_feature_flags_table(bind) -> None:
    inspector = sa.inspect(bind)
    if inspector.has_table("feature_flags"):
        return
    flag_status = pg.ENUM(
        "disabled",
        "testers",
        "premium",
        "all",
        "custom",
        name="feature_flag_status",
        create_type=False,
    )
    _ensure_enum(bind, flag_status)
    op.create_table(
        "feature_flags",
        sa.Column("slug", sa.Text(), primary_key=True),
        sa.Column("description", sa.Text()),
        sa.Column("status", flag_status, nullable=False, server_default="disabled"),
        sa.Column("rollout", sa.SmallInteger()),
        sa.Column("meta", pg.JSONB(astext_type=sa.Text())),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("created_by", sa.Text()),
        sa.Column("updated_by", sa.Text()),
    )


def _ensure_feature_flag_rules_table(bind) -> None:
    inspector = sa.inspect(bind)
    if inspector.has_table("feature_flag_rules"):
        return
    rule_type = pg.ENUM(
        "user",
        "segment",
        "role",
        "percentage",
        name="feature_flag_rule_type",
        create_type=False,
    )
    _ensure_enum(bind, rule_type)
    op.create_table(
        "feature_flag_rules",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("flag_slug", sa.Text(), nullable=False),
        sa.Column("type", rule_type, nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("rollout", sa.SmallInteger()),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("meta", pg.JSONB(astext_type=sa.Text())),
        sa.ForeignKeyConstraint(["flag_slug"], ["feature_flags.slug"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_feature_flag_rules_flag_slug_priority",
        "feature_flag_rules",
        ["flag_slug", "priority", "type", "value"],
        unique=False,
    )


def _ensure_feature_flag_audit_table(bind) -> None:
    inspector = sa.inspect(bind)
    if inspector.has_table("feature_flag_audit"):
        return
    op.create_table(
        "feature_flag_audit",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("flag_slug", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("actor_id", sa.Text()),
        sa.Column(
            "payload",
            pg.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["flag_slug"], ["feature_flags.slug"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_feature_flag_audit_flag_created",
        "feature_flag_audit",
        ["flag_slug", "created_at"],
        unique=False,
    )


def upgrade() -> None:
    bind = op.get_bind()
    _ensure_feature_flags_table(bind)
    _ensure_feature_flag_rules_table(bind)
    _ensure_feature_flag_audit_table(bind)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table("feature_flag_audit"):
        op.drop_index("ix_feature_flag_audit_flag_created", table_name="feature_flag_audit")
        op.drop_table("feature_flag_audit")
    if inspector.has_table("feature_flag_rules"):
        op.drop_index("ix_feature_flag_rules_flag_slug_priority", table_name="feature_flag_rules")
        op.drop_table("feature_flag_rules")
    if inspector.has_table("feature_flags"):
        op.drop_table("feature_flags")
