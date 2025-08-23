"""create core domain tables: payments, premium, ai logs

Revision ID: 20250820_domains_core_tables
Revises: 20250820_ai_generation_idx
Create Date: 2025-08-20

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20250820_domains_core_tables"
down_revision = "20250820_ai_generation_idx"
branch_labels = None
depends_on = None


def _safe_create_table(name: str, *cols, **kw) -> None:
    try:
        op.create_table(name, *cols, **kw)
    except Exception:
        # table may already exist (create_all in dev)
        pass


def _safe_create_index(name: str, table: str, cols: list[str]) -> None:
    try:
        op.create_index(name, table, cols)
    except Exception:
        pass


def upgrade() -> None:
    # payment_gateways
    _safe_create_table(
        "payment_gateways",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("type", sa.String(64), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("priority", sa.Integer(), nullable=False, server_default=sa.text("100")),
        sa.Column("config", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # payment_transactions
    _safe_create_table(
        "payment_transactions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), nullable=False, index=True),
        sa.Column("gateway_slug", sa.String(255), nullable=True, index=True),
        sa.Column("product_type", sa.String(64), nullable=False),
        sa.Column("product_id", sa.String(64), nullable=True, index=True),
        sa.Column("currency", sa.String(16), nullable=True),
        sa.Column("gross_cents", sa.Integer(), nullable=False),
        sa.Column("fee_cents", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("net_cents", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default=sa.text("'captured'")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("meta", sa.Text(), nullable=True),
    )

    # subscription_plans
    _safe_create_table(
        "subscription_plans",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("slug", sa.String(64), nullable=False, unique=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price_cents", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(16), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("order", sa.Integer(), nullable=False, server_default=sa.text("100")),
        sa.Column("monthly_limits", sa.Text(), nullable=True),
        sa.Column("features", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # user_subscriptions
    _safe_create_table(
        "user_subscriptions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), nullable=False, index=True),
        sa.Column("plan_id", sa.String(64), nullable=False, index=True),
        sa.Column("status", sa.String(32), nullable=False, server_default=sa.text("'active'")),
        sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ends_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        # простые внешние ключи в виде индекса; можно усилить FK в отдельных миграциях, если БД это поддерживает
    )

    # generation_job_logs
    _safe_create_table(
        "generation_job_logs",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("job_id", sa.String(64), nullable=False, index=True),
        sa.Column("stage", sa.String(32), nullable=False),
        sa.Column("provider", sa.String(64), nullable=True),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("raw_response", sa.Text(), nullable=True),
        sa.Column("usage", sa.Text(), nullable=True),
        sa.Column("cost", sa.Float(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default=sa.text("'ok'")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    _safe_create_index("ix_generation_job_logs_job_id", "generation_job_logs", ["job_id"])


def downgrade() -> None:
    # При откате пытаемся удалить созданные таблицы. Если используются — БД может не позволить, это нормально для dev.
    for name in [
        "generation_job_logs",
        "user_subscriptions",
        "subscription_plans",
        "payment_transactions",
        "payment_gateways",
    ]:
        try:
            op.drop_table(name)
        except Exception:
            pass
