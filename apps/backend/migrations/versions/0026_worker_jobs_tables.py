"""create worker jobs tables

Revision ID: 0026
Revises: 0025
Create Date: 2025-09-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision: str = "0026"
down_revision: str | None = "0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "worker_jobs",
        sa.Column("job_id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="queued"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("idempotency_key", sa.Text(), nullable=True),
        sa.Column("code_version", sa.Text(), nullable=True),
        sa.Column("model_version", sa.Text(), nullable=True),
        sa.Column("config_hash", sa.Text(), nullable=True),
        sa.Column("lease_until", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("lease_owner", sa.Text(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column(
            "available_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("cost_cap_eur", sa.Numeric(10, 2), nullable=True),
        sa.Column("budget_tag", sa.Text(), nullable=True),
        sa.Column("input", pg.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("result", pg.JSONB(astext_type=sa.Text()), nullable=True),
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
        "ix_worker_jobs_status_available",
        "worker_jobs",
        ["status", "available_at", "priority", "created_at"],
    )
    op.create_index(
        "ix_worker_jobs_lease_until",
        "worker_jobs",
        ["lease_until"],
    )
    op.create_unique_constraint(
        "uq_worker_jobs_idempotency",
        "worker_jobs",
        ["tenant_id", "type", "idempotency_key"],
    )

    op.create_table(
        "worker_job_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("job_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "ts",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("event", sa.Text(), nullable=False),
        sa.Column("details", pg.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["worker_jobs.job_id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_worker_job_events_job_id_ts",
        "worker_job_events",
        ["job_id", "ts"],
    )

    op.create_table(
        "worker_registry",
        sa.Column("worker_id", sa.Text(), primary_key=True),
        sa.Column("type", sa.Text(), nullable=True),
        sa.Column("code_version", sa.Text(), nullable=True),
        sa.Column("resource_class", sa.Text(), nullable=True),
        sa.Column("health", sa.Text(), nullable=True),
        sa.Column("last_heartbeat", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("zone", sa.Text(), nullable=True),
        sa.Column("meta", pg.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("worker_registry")
    op.drop_index("ix_worker_job_events_job_id_ts", table_name="worker_job_events")
    op.drop_table("worker_job_events")
    op.drop_index("ix_worker_jobs_lease_until", table_name="worker_jobs")
    op.drop_index("ix_worker_jobs_status_available", table_name="worker_jobs")
    op.drop_constraint("uq_worker_jobs_idempotency", "worker_jobs", type_="unique")
    op.drop_table("worker_jobs")
