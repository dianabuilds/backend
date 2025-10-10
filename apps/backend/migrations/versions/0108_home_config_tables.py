"""Create tables for home page configuration and audit.

Revision ID: 0108_home_config_tables
Revises: 0107_nodes_embedding_status
Create Date: 2025-10-10
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision = "0108_home_config_tables"
down_revision = "0107_nodes_embedding_status"
branch_labels = None
depends_on = None


HOME_CONFIG_STATUS = "home_config_status"


def _ensure_pgcrypto_extension() -> None:
    try:
        op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    except Exception:
        # Extension creation may fail on hosted Postgres or read-only roles.
        pass


def _create_home_config_status_enum(bind: sa.engine.Connection) -> pg.ENUM:
    enum = pg.ENUM(
        "draft",
        "published",
        name=HOME_CONFIG_STATUS,
        create_type=False,
    )
    enum.create(bind, checkfirst=True)
    return enum


def _has_index(inspector: sa.Inspector, table: str, name: str) -> bool:
    try:
        indexes = inspector.get_indexes(table)
    except Exception:
        return False
    return any(idx.get("name") == name for idx in indexes)


def upgrade() -> None:
    bind = op.get_bind()
    if bind is None:
        raise RuntimeError("Alembic connection is unavailable")

    inspector = sa.inspect(bind)

    _ensure_pgcrypto_extension()
    status_enum = _create_home_config_status_enum(bind)

    if not inspector.has_table("product_home_configs"):
        op.create_table(
            "product_home_configs",
            sa.Column(
                "id",
                pg.UUID(as_uuid=True),
                primary_key=True,
                nullable=False,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("slug", sa.Text(), nullable=False),
            sa.Column(
                "version",
                sa.BigInteger(),
                nullable=False,
                server_default=sa.text("1"),
            ),
            sa.Column(
                "status",
                status_enum,
                nullable=False,
                server_default=sa.text("'draft'"),
            ),
            sa.Column(
                "data",
                pg.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
            sa.Column("created_by", sa.Text(), nullable=True),
            sa.Column("updated_by", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("draft_of", pg.UUID(as_uuid=True), nullable=True),
            sa.ForeignKeyConstraint(
                ["draft_of"],
                ["product_home_configs.id"],
                ondelete="SET NULL",
                name="fk_product_home_configs_draft_of",
                use_alter=True,
            ),
            sa.UniqueConstraint("slug", name="ux_product_home_configs_slug"),
        )
        op.create_index(
            "ix_product_home_configs_status",
            "product_home_configs",
            ["status"],
        )
        op.create_index(
            "ix_product_home_configs_slug_status",
            "product_home_configs",
            ["slug", "status"],
            unique=False,
            postgresql_where=sa.text("status = 'published'"),
        )

    if not inspector.has_table("home_config_audits"):
        op.create_table(
            "home_config_audits",
            sa.Column(
                "id",
                pg.UUID(as_uuid=True),
                primary_key=True,
                nullable=False,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("config_id", pg.UUID(as_uuid=True), nullable=False),
            sa.Column("version", sa.BigInteger(), nullable=False),
            sa.Column("action", sa.Text(), nullable=False),
            sa.Column("actor", sa.Text(), nullable=True),
            sa.Column("actor_team", sa.Text(), nullable=True),
            sa.Column(
                "data",
                pg.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
            sa.Column(
                "diff",
                pg.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.ForeignKeyConstraint(
                ["config_id"],
                ["product_home_configs.id"],
                ondelete="CASCADE",
                name="fk_home_config_audits_config",
            ),
        )
        op.create_index(
            "ix_home_config_audits_config_id",
            "home_config_audits",
            ["config_id", "version"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind is None:
        raise RuntimeError("Alembic connection is unavailable")

    inspector = sa.inspect(bind)

    if _has_index(inspector, "home_config_audits", "ix_home_config_audits_config_id"):
        op.drop_index(
            "ix_home_config_audits_config_id",
            table_name="home_config_audits",
        )
    if inspector.has_table("home_config_audits"):
        op.drop_table("home_config_audits")

    if _has_index(
        inspector, "product_home_configs", "ix_product_home_configs_slug_status"
    ):
        op.drop_index(
            "ix_product_home_configs_slug_status",
            table_name="product_home_configs",
        )
    if _has_index(inspector, "product_home_configs", "ix_product_home_configs_status"):
        op.drop_index(
            "ix_product_home_configs_status",
            table_name="product_home_configs",
        )
    if inspector.has_table("product_home_configs"):
        op.drop_table("product_home_configs")

    status_enum = pg.ENUM(
        "draft",
        "published",
        name=HOME_CONFIG_STATUS,
        create_type=False,
    )
    status_enum.drop(bind, checkfirst=True)
