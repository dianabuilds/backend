"""feature flags sql store

Revision ID: 0101_feature_flags_sql
Revises: 0100_squashed_base
Create Date: 2025-09-30
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision = "0101_feature_flags_sql"
down_revision = "0100_squashed_base"
branch_labels = None
depends_on = None

LEGACY_FLAG_SIGNATURE = {"key", "enabled", "payload"}
KNOWN_PAYLOAD_KEYS = {"description", "rollout", "users", "roles", "meta", "segments"}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    flag_status = pg.ENUM(
        "disabled",
        "testers",
        "premium",
        "all",
        "custom",
        name="feature_flag_status",
        create_type=False,
    )
    rule_type = pg.ENUM(
        "user",
        "segment",
        "role",
        "percentage",
        name="feature_flag_rule_type",
        create_type=False,
    )

    flag_status.create(bind, checkfirst=True)
    rule_type.create(bind, checkfirst=True)

    migrated_legacy = False
    if inspector.has_table("feature_flags"):
        columns = {column["name"] for column in inspector.get_columns("feature_flags")}
        if LEGACY_FLAG_SIGNATURE.issubset(columns):
            _migrate_legacy_flags(bind, flag_status, rule_type)
            migrated_legacy = True

    if migrated_legacy:
        inspector = sa.inspect(bind)

    if not inspector.has_table("feature_flags"):
        _create_feature_flags_table(flag_status)
    if not inspector.has_table("feature_flag_rules"):
        _create_feature_flag_rules_table(rule_type)
    if not inspector.has_table("feature_flag_audit"):
        _create_feature_flag_audit_table()

    _ensure_feature_flags_index(bind)
    _ensure_feature_flag_rules_indexes(bind)
    _ensure_feature_flag_audit_index(bind)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    flag_rows: list[dict[str, object]] = []
    rule_rows: list[dict[str, object]] = []

    if inspector.has_table("feature_flags"):
        flags_table = sa.Table("feature_flags", sa.MetaData(), autoload_with=bind)
        flag_rows = list(
            bind.execute(
                sa.select(
                    flags_table.c.slug,
                    flags_table.c.description,
                    flags_table.c.status,
                    flags_table.c.rollout,
                    flags_table.c.meta,
                    flags_table.c.created_at,
                    flags_table.c.updated_at,
                    flags_table.c.created_by,
                    flags_table.c.updated_by,
                )
            ).mappings()
        )
    if inspector.has_table("feature_flag_rules"):
        rules_table = sa.Table("feature_flag_rules", sa.MetaData(), autoload_with=bind)
        rule_rows = list(
            bind.execute(
                sa.select(
                    rules_table.c.flag_slug,
                    rules_table.c.type,
                    rules_table.c.value,
                    rules_table.c.rollout,
                    rules_table.c.priority,
                    rules_table.c.meta,
                )
            ).mappings()
        )

    legacy_rows = _build_legacy_rows(flag_rows, rule_rows)

    if inspector.has_table("feature_flag_audit"):
        op.drop_table("feature_flag_audit")
    if inspector.has_table("feature_flag_rules"):
        op.drop_table("feature_flag_rules")
    if inspector.has_table("feature_flags"):
        op.drop_table("feature_flags")

    rule_type = pg.ENUM(
        "user",
        "segment",
        "role",
        "percentage",
        name="feature_flag_rule_type",
        create_type=False,
    )
    flag_status = pg.ENUM(
        "disabled",
        "testers",
        "premium",
        "all",
        "custom",
        name="feature_flag_status",
        create_type=False,
    )
    rule_type.drop(bind, checkfirst=True)
    flag_status.drop(bind, checkfirst=True)

    legacy_table = op.create_table(
        "feature_flags",
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("key", sa.Text(), nullable=False, unique=True),
        sa.Column(
            "enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("payload", pg.JSONB(astext_type=sa.Text())),
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

    if legacy_rows:
        bind.execute(legacy_table.insert(), legacy_rows)


def _create_feature_flags_table(flag_status: pg.ENUM) -> None:
    op.create_table(
        "feature_flags",
        sa.Column("slug", sa.Text(), primary_key=True),
        sa.Column("description", sa.Text()),
        sa.Column("status", flag_status, nullable=False, server_default="disabled"),
        sa.Column("rollout", sa.SmallInteger()),
        sa.Column(
            "meta",
            pg.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("created_by", sa.Text()),
        sa.Column("updated_by", sa.Text()),
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
    op.create_index("ix_feature_flags_status", "feature_flags", ["status"])


def _create_feature_flag_rules_table(rule_type: pg.ENUM) -> None:
    op.create_table(
        "feature_flag_rules",
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "flag_slug",
            sa.Text(),
            sa.ForeignKey("feature_flags.slug", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", rule_type, nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("rollout", sa.SmallInteger()),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column(
            "meta",
            pg.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.create_index(
        "ix_feature_flag_rules_flag_type",
        "feature_flag_rules",
        ["flag_slug", "type"],
    )
    op.create_index(
        "ix_feature_flag_rules_priority",
        "feature_flag_rules",
        ["flag_slug", "priority"],
    )


def _create_feature_flag_audit_table() -> None:
    op.create_table(
        "feature_flag_audit",
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("flag_slug", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column(
            "payload",
            pg.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("actor_id", sa.Text()),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_feature_flag_audit_flag", "feature_flag_audit", ["flag_slug"])


def _ensure_feature_flags_index(bind: sa.engine.Connection) -> None:
    if not sa.inspect(bind).has_table("feature_flags"):
        return
    bind.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_feature_flags_status "
            "ON feature_flags (status)"
        )
    )


def _ensure_feature_flag_rules_indexes(bind: sa.engine.Connection) -> None:
    if not sa.inspect(bind).has_table("feature_flag_rules"):
        return
    bind.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_feature_flag_rules_flag_type "
            "ON feature_flag_rules (flag_slug, type)"
        )
    )
    bind.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_feature_flag_rules_priority "
            "ON feature_flag_rules (flag_slug, priority)"
        )
    )


def _ensure_feature_flag_audit_index(bind: sa.engine.Connection) -> None:
    if not sa.inspect(bind).has_table("feature_flag_audit"):
        return
    bind.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_feature_flag_audit_flag "
            "ON feature_flag_audit (flag_slug)"
        )
    )


def _migrate_legacy_flags(
    bind: sa.engine.Connection,
    flag_status: pg.ENUM,
    rule_type: pg.ENUM,
) -> None:
    legacy_table_name = "feature_flags_legacy"
    op.rename_table("feature_flags", legacy_table_name)

    _create_feature_flags_table(flag_status)
    _create_feature_flag_rules_table(rule_type)
    _create_feature_flag_audit_table()

    legacy_table = sa.Table(legacy_table_name, sa.MetaData(), autoload_with=bind)

    flags_table = sa.table(
        "feature_flags",
        sa.column("slug", sa.Text()),
        sa.column("description", sa.Text()),
        sa.column("status", flag_status),
        sa.column("rollout", sa.SmallInteger()),
        sa.column("meta", pg.JSONB(astext_type=sa.Text())),
        sa.column("created_at", sa.TIMESTAMP(timezone=True)),
        sa.column("updated_at", sa.TIMESTAMP(timezone=True)),
        sa.column("created_by", sa.Text()),
        sa.column("updated_by", sa.Text()),
    )
    rules_table = sa.table(
        "feature_flag_rules",
        sa.column("flag_slug", sa.Text()),
        sa.column("type", rule_type),
        sa.column("value", sa.Text()),
        sa.column("rollout", sa.SmallInteger()),
        sa.column("priority", sa.Integer()),
        sa.column("meta", pg.JSONB(astext_type=sa.Text())),
    )

    from domains.platform.flags.application.mapper import feature_from_legacy
    from domains.platform.flags.domain.models import Flag

    flag_rows: list[dict[str, object]] = []
    rule_rows: list[dict[str, object]] = []

    for row in bind.execute(
        sa.select(
            legacy_table.c.key,
            legacy_table.c.enabled,
            legacy_table.c.payload,
            legacy_table.c.created_at,
            legacy_table.c.updated_at,
        )
    ).mappings():
        payload = row["payload"] or {}
        if not isinstance(payload, dict):
            payload = {}
        meta = {}
        payload_meta = payload.get("meta")
        if isinstance(payload_meta, dict):
            meta.update(payload_meta)
        extra_meta = {k: v for k, v in payload.items() if k not in KNOWN_PAYLOAD_KEYS}
        if extra_meta:
            meta.update(extra_meta)
        rollout_value = payload.get("rollout")
        try:
            rollout = int(rollout_value) if rollout_value is not None else None
        except (TypeError, ValueError):
            rollout = None
        if rollout is None:
            rollout = 100 if row["enabled"] else 0
        users = payload.get("users") or []
        roles = payload.get("roles") or []
        legacy_flag = Flag(
            slug=row["key"],
            enabled=row["enabled"],
            description=payload.get("description"),
            rollout=int(rollout),
            users=set(users),
            roles=set(roles),
            meta=meta or None,
        )
        feature_flag = feature_from_legacy(legacy_flag)
        created_at = row["created_at"] or datetime.utcnow()
        updated_at = row["updated_at"] or created_at
        flag_rows.append(
            {
                "slug": feature_flag.slug,
                "description": feature_flag.description,
                "status": feature_flag.status.value,
                "rollout": feature_flag.rollout,
                "meta": feature_flag.meta or {},
                "created_at": created_at,
                "updated_at": updated_at,
                "created_by": None,
                "updated_by": None,
            }
        )
        for rule in feature_flag.rules:
            rule_rows.append(
                {
                    "flag_slug": feature_flag.slug,
                    "type": rule.type.value,
                    "value": rule.value,
                    "rollout": rule.rollout,
                    "priority": rule.priority,
                    "meta": rule.meta or {},
                }
            )

    if flag_rows:
        bind.execute(sa.insert(flags_table), flag_rows)
    if rule_rows:
        bind.execute(sa.insert(rules_table), rule_rows)

    op.drop_table(legacy_table_name)


def _build_legacy_rows(
    flag_rows: list[dict[str, object]],
    rule_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    if not flag_rows:
        return []

    from domains.platform.flags.application.mapper import legacy_from_feature
    from domains.platform.flags.domain.models import (
        FeatureFlag,
        FlagRule,
        FlagRuleType,
        FlagStatus,
    )

    rules_by_slug: defaultdict[str, list[dict[str, object]]] = defaultdict(list)
    for rule in rule_rows:
        key = str(rule.get("flag_slug") or "")
        rules_by_slug[key].append(rule)

    legacy_entries: list[dict[str, object]] = []
    for row in flag_rows:
        slug = str(row["slug"])
        feature_flag = FeatureFlag(
            slug=slug,
            description=row["description"],
            status=FlagStatus(row["status"]),
            rollout=row["rollout"],
            meta=row["meta"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            created_by=row["created_by"],
            updated_by=row["updated_by"],
            rules=tuple(
                sorted(
                    (
                        FlagRule(
                            type=FlagRuleType(rule["type"]),
                            value=rule["value"],
                            rollout=rule["rollout"],
                            priority=rule["priority"],
                            meta=rule["meta"],
                        )
                        for rule in rules_by_slug.get(slug, [])
                    ),
                    key=lambda item: (item.priority, item.type.value, item.value),
                )
            ),
        )
        legacy_flag = legacy_from_feature(feature_flag)
        payload: dict[str, object] = {}
        if legacy_flag.description is not None:
            payload["description"] = legacy_flag.description
        if legacy_flag.rollout is not None:
            payload["rollout"] = legacy_flag.rollout
        if legacy_flag.users:
            payload["users"] = sorted(legacy_flag.users)
        if legacy_flag.roles:
            payload["roles"] = sorted(legacy_flag.roles)
        if legacy_flag.meta:
            payload["meta"] = legacy_flag.meta
        created_at = row["created_at"] or datetime.utcnow()
        updated_at = row["updated_at"] or created_at
        legacy_entries.append(
            {
                "id": uuid.uuid4(),
                "key": legacy_flag.slug,
                "enabled": legacy_flag.enabled,
                "payload": payload or None,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
    return legacy_entries
