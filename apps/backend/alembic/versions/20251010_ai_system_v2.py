"""AI system v2 tables: providers, models, profiles, presets, defaults, evals

Revision ID: 20251010_ai_system_v2
Revises: 20250930_remove_user_workspace_fields
Create Date: 2025-10-10
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20251010_ai_system_v2"
down_revision = "20250930_remove_user_workspace_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_providers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(), nullable=False, unique=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("base_url", sa.String(), nullable=True),
        sa.Column("manifest", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("health", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "ai_provider_secrets",
        sa.Column(
            "provider_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ai_providers.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("key", sa.String(), primary_key=True),
        sa.Column("value_encrypted", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "ai_models",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "provider_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ai_providers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("family", sa.String(), nullable=True),
        sa.Column("capabilities", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("inputs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("limits", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("pricing", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("provider_id", "code", name="uq_ai_models_provider_code"),
    )
    # GIN indexes for JSONB columns
    op.create_index(
        "ix_ai_models_capabilities_gin", "ai_models", ["capabilities"], postgresql_using="gin"
    )
    op.create_index("ix_ai_models_inputs_gin", "ai_models", ["inputs"], postgresql_using="gin")

    op.create_table(
        "ai_defaults",
        sa.Column("id", sa.String(), primary_key=True, server_default="1"),
        sa.Column(
            "provider_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ai_providers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "model_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ai_models.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("bundle_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    op.create_table(
        "ai_routing_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("rules", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_ai_routing_profiles_rules_gin", "ai_routing_profiles", ["rules"], postgresql_using="gin"
    )

    op.create_table(
        "ai_presets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("task", sa.String(), nullable=False),
        sa.Column("params", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "ai_eval_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ai_routing_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("spec", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("stats", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:  # pragma: no cover
    op.drop_table("ai_eval_runs")
    op.drop_table("ai_presets")
    op.drop_index("ix_ai_routing_profiles_rules_gin", table_name="ai_routing_profiles")
    op.drop_table("ai_routing_profiles")
    op.drop_table("ai_defaults")
    op.drop_index("ix_ai_models_inputs_gin", table_name="ai_models")
    op.drop_index("ix_ai_models_capabilities_gin", table_name="ai_models")
    op.drop_table("ai_models")
    op.drop_table("ai_provider_secrets")
    op.drop_table("ai_providers")
