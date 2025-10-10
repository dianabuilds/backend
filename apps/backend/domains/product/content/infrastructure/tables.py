from __future__ import annotations

import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from domains.product.content.domain import HomeConfigStatus

metadata = sa.MetaData()


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _enum_values(enum_cls: type[HomeConfigStatus]) -> list[str]:
    return [member.value for member in enum_cls]


_status_enum = sa.Enum(
    HomeConfigStatus,
    name="home_config_status",
    values_callable=_enum_values,
    native_enum=False,
    validate_strings=True,
)
_status_enum = _status_enum.with_variant(
    pg.ENUM(
        HomeConfigStatus,
        name="home_config_status",
        values_callable=_enum_values,
        validate_strings=True,
        create_type=False,
    ),
    "postgresql",
)

_json_type = sa.JSON().with_variant(
    pg.JSONB(astext_type=sa.Text()),
    "postgresql",
)


PRODUCT_HOME_CONFIGS_TABLE = sa.Table(
    "product_home_configs",
    metadata,
    sa.Column(
        "id",
        sa.Uuid(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=uuid.uuid4,
    ),
    sa.Column("slug", sa.Text(), nullable=False),
    sa.Column(
        "version",
        sa.BigInteger(),
        nullable=False,
        default=0,
    ),
    sa.Column(
        "status",
        _status_enum,
        nullable=False,
        default=HomeConfigStatus.DRAFT.value,
    ),
    sa.Column(
        "data",
        _json_type,
        nullable=False,
        default=dict,
    ),
    sa.Column("created_by", sa.Text(), nullable=True),
    sa.Column("updated_by", sa.Text(), nullable=True),
    sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    ),
    sa.Column(
        "updated_at",
        sa.DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    ),
    sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column(
        "draft_of",
        sa.Uuid(as_uuid=True),
        sa.ForeignKey(
            "product_home_configs.id",
            ondelete="SET NULL",
            name="fk_product_home_configs_draft_of",
            use_alter=True,
        ),
        nullable=True,
    ),
)

sa.Index(
    "ix_product_home_configs_status",
    PRODUCT_HOME_CONFIGS_TABLE.c.status,
)
sa.Index(
    "ix_product_home_configs_slug_status",
    PRODUCT_HOME_CONFIGS_TABLE.c.slug,
    PRODUCT_HOME_CONFIGS_TABLE.c.status,
    postgresql_where=(
        PRODUCT_HOME_CONFIGS_TABLE.c.status == HomeConfigStatus.PUBLISHED.value
    ),
)

HOME_CONFIG_AUDITS_TABLE = sa.Table(
    "home_config_audits",
    metadata,
    sa.Column(
        "id",
        sa.Uuid(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=uuid.uuid4,
    ),
    sa.Column(
        "config_id",
        sa.Uuid(as_uuid=True),
        sa.ForeignKey(
            "product_home_configs.id",
            ondelete="CASCADE",
            name="fk_home_config_audits_config",
        ),
        nullable=False,
    ),
    sa.Column("version", sa.BigInteger(), nullable=False),
    sa.Column("action", sa.Text(), nullable=False),
    sa.Column("actor", sa.Text(), nullable=True),
    sa.Column("actor_team", sa.Text(), nullable=True),
    sa.Column("comment", sa.Text(), nullable=True),
    sa.Column("data", _json_type, nullable=True),
    sa.Column("diff", _json_type, nullable=True),
    sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    ),
)

sa.Index(
    "ix_home_config_audits_config_id",
    HOME_CONFIG_AUDITS_TABLE.c.config_id,
    HOME_CONFIG_AUDITS_TABLE.c.version,
)


__all__ = [
    "PRODUCT_HOME_CONFIGS_TABLE",
    "HOME_CONFIG_AUDITS_TABLE",
    "metadata",
]
