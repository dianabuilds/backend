"""postgres types upgrade: UUID/JSONB/TIMESTAMPTZ on core domain tables

Revision ID: 20250820_pg_types_upgrade
Revises: 20250820_domains_core_tables
Create Date: 2025-08-20

"""
from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = "20250820_pg_types_upgrade"
down_revision = "20250820_domains_core_tables"
branch_labels = None
depends_on = None


def _is_postgres() -> bool:
    bind = op.get_bind()
    return getattr(getattr(bind, "dialect", None), "name", "") == "postgresql"


def upgrade() -> None:
    if not _is_postgres():
        return

    # payment_transactions
    for stmt in [
        "ALTER TABLE payment_transactions ALTER COLUMN id TYPE uuid USING id::uuid",
        "ALTER TABLE payment_transactions ALTER COLUMN user_id TYPE uuid USING user_id::uuid",
        "ALTER TABLE payment_transactions ALTER COLUMN product_id TYPE uuid USING product_id::uuid",
        "ALTER TABLE payment_transactions ALTER COLUMN meta TYPE jsonb USING meta::jsonb",
        "ALTER TABLE payment_transactions ALTER COLUMN created_at TYPE timestamptz USING created_at::timestamptz",
    ]:
        try:
            op.execute(stmt)
        except Exception:
            pass

    # payment_gateways
    for stmt in [
        "ALTER TABLE payment_gateways ALTER COLUMN id TYPE uuid USING id::uuid",
        "ALTER TABLE payment_gateways ALTER COLUMN config TYPE jsonb USING config::jsonb",
        "ALTER TABLE payment_gateways ALTER COLUMN created_at TYPE timestamptz USING created_at::timestamptz",
        "ALTER TABLE payment_gateways ALTER COLUMN updated_at TYPE timestamptz USING updated_at::timestamptz",
    ]:
        try:
            op.execute(stmt)
        except Exception:
            pass

    # subscription_plans
    for stmt in [
        "ALTER TABLE subscription_plans ALTER COLUMN id TYPE uuid USING id::uuid",
        "ALTER TABLE subscription_plans ALTER COLUMN monthly_limits TYPE jsonb USING monthly_limits::jsonb",
        "ALTER TABLE subscription_plans ALTER COLUMN features TYPE jsonb USING features::jsonb",
        "ALTER TABLE subscription_plans ALTER COLUMN created_at TYPE timestamptz USING created_at::timestamptz",
        "ALTER TABLE subscription_plans ALTER COLUMN updated_at TYPE timestamptz USING updated_at::timestamptz",
    ]:
        try:
            op.execute(stmt)
        except Exception:
            pass

    # user_subscriptions
    for stmt in [
        "ALTER TABLE user_subscriptions ALTER COLUMN id TYPE uuid USING id::uuid",
        "ALTER TABLE user_subscriptions ALTER COLUMN user_id TYPE uuid USING user_id::uuid",
        "ALTER TABLE user_subscriptions ALTER COLUMN plan_id TYPE uuid USING plan_id::uuid",
        "ALTER TABLE user_subscriptions ALTER COLUMN started_at TYPE timestamptz USING started_at::timestamptz",
        "ALTER TABLE user_subscriptions ALTER COLUMN ends_at TYPE timestamptz USING ends_at::timestamptz",
        "ALTER TABLE user_subscriptions ALTER COLUMN created_at TYPE timestamptz USING created_at::timestamptz",
        "ALTER TABLE user_subscriptions ALTER COLUMN updated_at TYPE timestamptz USING updated_at::timestamptz",
    ]:
        try:
            op.execute(stmt)
        except Exception:
            pass

    # generation_job_logs
    for stmt in [
        "ALTER TABLE generation_job_logs ALTER COLUMN id TYPE uuid USING id::uuid",
        "ALTER TABLE generation_job_logs ALTER COLUMN job_id TYPE uuid USING job_id::uuid",
        "ALTER TABLE generation_job_logs ALTER COLUMN usage TYPE jsonb USING usage::jsonb",
        "ALTER TABLE generation_job_logs ALTER COLUMN created_at TYPE timestamptz USING created_at::timestamptz",
    ]:
        try:
            op.execute(stmt)
        except Exception:
            pass


def downgrade() -> None:
    if not _is_postgres():
        return

    # payment_transactions back to text/timestamp
    for stmt in [
        "ALTER TABLE payment_transactions ALTER COLUMN id TYPE text USING id::text",
        "ALTER TABLE payment_transactions ALTER COLUMN user_id TYPE text USING user_id::text",
        "ALTER TABLE payment_transactions ALTER COLUMN product_id TYPE text USING product_id::text",
        "ALTER TABLE payment_transactions ALTER COLUMN meta TYPE text USING meta::text",
        "ALTER TABLE payment_transactions ALTER COLUMN created_at TYPE timestamp USING created_at::timestamp",
    ]:
        try:
            op.execute(stmt)
        except Exception:
            pass

    # payment_gateways
    for stmt in [
        "ALTER TABLE payment_gateways ALTER COLUMN id TYPE text USING id::text",
        "ALTER TABLE payment_gateways ALTER COLUMN config TYPE text USING config::text",
        "ALTER TABLE payment_gateways ALTER COLUMN created_at TYPE timestamp USING created_at::timestamp",
        "ALTER TABLE payment_gateways ALTER COLUMN updated_at TYPE timestamp USING updated_at::timestamp",
    ]:
        try:
            op.execute(stmt)
        except Exception:
            pass

    # subscription_plans
    for stmt in [
        "ALTER TABLE subscription_plans ALTER COLUMN id TYPE text USING id::text",
        "ALTER TABLE subscription_plans ALTER COLUMN monthly_limits TYPE text USING monthly_limits::text",
        "ALTER TABLE subscription_plans ALTER COLUMN features TYPE text USING features::text",
        "ALTER TABLE subscription_plans ALTER COLUMN created_at TYPE timestamp USING created_at::timestamp",
        "ALTER TABLE subscription_plans ALTER COLUMN updated_at TYPE timestamp USING updated_at::timestamp",
    ]:
        try:
            op.execute(stmt)
        except Exception:
            pass

    # user_subscriptions
    for stmt in [
        "ALTER TABLE user_subscriptions ALTER COLUMN id TYPE text USING id::text",
        "ALTER TABLE user_subscriptions ALTER COLUMN user_id TYPE text USING user_id::text",
        "ALTER TABLE user_subscriptions ALTER COLUMN plan_id TYPE text USING plan_id::text",
        "ALTER TABLE user_subscriptions ALTER COLUMN started_at TYPE timestamp USING started_at::timestamp",
        "ALTER TABLE user_subscriptions ALTER COLUMN ends_at TYPE timestamp USING ends_at::timestamp",
        "ALTER TABLE user_subscriptions ALTER COLUMN created_at TYPE timestamp USING created_at::timestamp",
        "ALTER TABLE user_subscriptions ALTER COLUMN updated_at TYPE timestamp USING updated_at::timestamp",
    ]:
        try:
            op.execute(stmt)
        except Exception:
            pass

    # generation_job_logs
    for stmt in [
        "ALTER TABLE generation_job_logs ALTER COLUMN id TYPE text USING id::text",
        "ALTER TABLE generation_job_logs ALTER COLUMN job_id TYPE text USING job_id::text",
        "ALTER TABLE generation_job_logs ALTER COLUMN usage TYPE text USING usage::text",
        "ALTER TABLE generation_job_logs ALTER COLUMN created_at TYPE timestamp USING created_at::timestamp",
    ]:
        try:
            op.execute(stmt)
        except Exception:
            pass
