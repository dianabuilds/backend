from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from domains.platform.flags.application.mapper import (
    feature_from_legacy,
    legacy_from_feature,
)
from domains.platform.flags.domain.models import (
    FeatureFlag,
    Flag,
    FlagRule,
    FlagRuleType,
    FlagStatus,
)
from domains.platform.flags.ports import FlagStore

_METADATA = sa.MetaData()


def _enum_values(enum_cls):
    return [member.value for member in enum_cls]


FLAGS_TABLE = sa.Table(
    "feature_flags",
    _METADATA,
    sa.Column("slug", sa.Text(), primary_key=True),
    sa.Column("description", sa.Text()),
    sa.Column(
        "status",
        sa.Enum(
            FlagStatus,
            name="feature_flag_status",
            values_callable=_enum_values,
            validate_strings=True,
        ),
    ),
    sa.Column("rollout", sa.SmallInteger()),
    sa.Column("meta", pg.JSONB(astext_type=sa.Text())),
    sa.Column("created_at", sa.TIMESTAMP(timezone=True)),
    sa.Column("updated_at", sa.TIMESTAMP(timezone=True)),
    sa.Column("created_by", sa.Text()),
    sa.Column("updated_by", sa.Text()),
)
RULES_TABLE = sa.Table(
    "feature_flag_rules",
    _METADATA,
    sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
    sa.Column("flag_slug", sa.Text()),
    sa.Column(
        "type",
        sa.Enum(
            FlagRuleType,
            name="feature_flag_rule_type",
            values_callable=_enum_values,
            validate_strings=True,
        ),
    ),
    sa.Column("value", sa.Text()),
    sa.Column("rollout", sa.SmallInteger()),
    sa.Column("priority", sa.Integer()),
    sa.Column("meta", pg.JSONB(astext_type=sa.Text())),
)


class FlagStoreSQL(FlagStore):
    """SQL-backed implementation of the flag store protocol."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def list(self) -> list[Flag]:
        async with self._session_factory() as session:
            flag_rows = (
                (
                    await session.execute(
                        select(
                            FLAGS_TABLE.c.slug,
                            FLAGS_TABLE.c.description,
                            FLAGS_TABLE.c.status,
                            FLAGS_TABLE.c.rollout,
                            FLAGS_TABLE.c.meta,
                            FLAGS_TABLE.c.created_at,
                            FLAGS_TABLE.c.updated_at,
                            FLAGS_TABLE.c.created_by,
                            FLAGS_TABLE.c.updated_by,
                        ).order_by(FLAGS_TABLE.c.slug)
                    )
                )
                .mappings()
                .all()
            )
            if not flag_rows:
                return []
            rule_rows = (
                (
                    await session.execute(
                        select(
                            RULES_TABLE.c.flag_slug,
                            RULES_TABLE.c.type,
                            RULES_TABLE.c.value,
                            RULES_TABLE.c.rollout,
                            RULES_TABLE.c.priority,
                            RULES_TABLE.c.meta,
                        ).order_by(
                            RULES_TABLE.c.flag_slug,
                            RULES_TABLE.c.priority,
                            RULES_TABLE.c.type,
                            RULES_TABLE.c.value,
                        )
                    )
                )
                .mappings()
                .all()
            )
        feature_flags = _hydrate_feature_flags(flag_rows, rule_rows)
        return [legacy_from_feature(flag) for flag in feature_flags]

    async def get(self, slug: str) -> Flag | None:
        async with self._session_factory() as session:
            row = (
                (
                    await session.execute(
                        select(
                            FLAGS_TABLE.c.slug,
                            FLAGS_TABLE.c.description,
                            FLAGS_TABLE.c.status,
                            FLAGS_TABLE.c.rollout,
                            FLAGS_TABLE.c.meta,
                            FLAGS_TABLE.c.created_at,
                            FLAGS_TABLE.c.updated_at,
                            FLAGS_TABLE.c.created_by,
                            FLAGS_TABLE.c.updated_by,
                        ).where(FLAGS_TABLE.c.slug == slug)
                    )
                )
                .mappings()
                .first()
            )
            if not row:
                return None
            rule_rows = (
                (
                    await session.execute(
                        select(
                            RULES_TABLE.c.flag_slug,
                            RULES_TABLE.c.type,
                            RULES_TABLE.c.value,
                            RULES_TABLE.c.rollout,
                            RULES_TABLE.c.priority,
                            RULES_TABLE.c.meta,
                        )
                        .where(RULES_TABLE.c.flag_slug == slug)
                        .order_by(
                            RULES_TABLE.c.priority,
                            RULES_TABLE.c.type,
                            RULES_TABLE.c.value,
                        )
                    )
                )
                .mappings()
                .all()
            )
        feature_flag = _hydrate_feature_flags([row], rule_rows)[0]
        return legacy_from_feature(feature_flag)

    async def upsert(self, flag: Flag) -> Flag:
        feature_flag = feature_from_legacy(flag)
        async with self._session_factory() as session:
            async with session.begin():
                await session.execute(_insert_flag_stmt(feature_flag))
                await session.execute(
                    RULES_TABLE.delete().where(RULES_TABLE.c.flag_slug == feature_flag.slug)
                )
                if feature_flag.rules:
                    await session.execute(
                        RULES_TABLE.insert(),
                        [
                            {
                                "flag_slug": feature_flag.slug,
                                "type": rule.type.value,
                                "value": rule.value,
                                "rollout": rule.rollout,
                                "priority": rule.priority,
                                "meta": rule.meta or {},
                            }
                            for rule in feature_flag.rules
                        ],
                    )
        return await self.get(flag.slug)  # type: ignore[return-value]

    async def delete(self, slug: str) -> None:
        async with self._session_factory() as session:
            async with session.begin():
                await session.execute(FLAGS_TABLE.delete().where(FLAGS_TABLE.c.slug == slug))


def _hydrate_feature_flags(flag_rows, rule_rows) -> list[FeatureFlag]:
    grouped_rules: dict[str, list[FlagRule]] = {}
    for mapping in rule_rows:
        slug = mapping["flag_slug"]
        raw_type = mapping.get("type")
        try:
            rule_type = FlagRuleType(raw_type)
        except Exception:
            continue
        grouped_rules.setdefault(slug, []).append(
            FlagRule(
                type=rule_type,
                value=mapping["value"],
                rollout=mapping["rollout"],
                priority=mapping["priority"],
                meta=dict(mapping["meta"] or {}),
            )
        )
    feature_flags: list[FeatureFlag] = []
    for row in flag_rows:
        slug = row["slug"]
        rules = tuple(
            sorted(
                grouped_rules.get(slug, []),
                key=lambda rule: (rule.priority, rule.type.value, rule.value),
            )
        )
        raw_status = row.get("status")
        try:
            status = FlagStatus(raw_status) if raw_status else FlagStatus.DISABLED
        except Exception:
            status = FlagStatus.DISABLED
        feature_flags.append(
            FeatureFlag(
                slug=slug,
                status=status,
                description=row["description"],
                rollout=row["rollout"],
                rules=rules,
                meta=dict(row["meta"] or {}),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                created_by=row["created_by"],
                updated_by=row["updated_by"],
            )
        )
    return feature_flags


def _insert_flag_stmt(flag: FeatureFlag):
    payload = {
        "slug": flag.slug,
        "description": flag.description,
        "status": flag.status.value,
        "rollout": flag.rollout,
        "meta": flag.meta or {},
    }
    stmt = insert(FLAGS_TABLE).values(**payload)
    return stmt.on_conflict_do_update(
        index_elements=[FLAGS_TABLE.c.slug],
        set_={
            "description": stmt.excluded.description,
            "status": stmt.excluded.status,
            "rollout": stmt.excluded.rollout,
            "meta": stmt.excluded.meta,
            "updated_at": sa.text("now()"),
        },
    )


__all__ = ["FlagStoreSQL"]
