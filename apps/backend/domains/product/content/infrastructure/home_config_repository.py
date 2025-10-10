from __future__ import annotations

import json
import uuid
from collections.abc import Awaitable, Mapping
from datetime import UTC, datetime
from typing import Any, Protocol

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from domains.product.content.domain import (
    HomeConfig,
    HomeConfigAudit,
    HomeConfigDraftNotFound,
    HomeConfigHistoryEntry,
    HomeConfigNotFound,
    HomeConfigRepositoryError,
    HomeConfigStatus,
)

from .tables import HOME_CONFIG_AUDITS_TABLE, PRODUCT_HOME_CONFIGS_TABLE


class EngineFactory(Protocol):
    def __call__(self) -> Awaitable[AsyncEngine | None]: ...


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _as_uuid(value: Any) -> uuid.UUID:
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


def _as_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    if value is None:
        return datetime.fromtimestamp(0, tz=UTC)
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return datetime.fromtimestamp(0, tz=UTC)


def _as_mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return {}
    return dict(value)


def _as_patch(value: Any) -> list[dict[str, Any]] | None:
    if value is None:
        return None
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return None
    if not isinstance(value, list):
        return None
    ops: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, Mapping):
            ops.append(dict(item))
    return ops


class HomeConfigRepository:
    """Persistence layer for home page configurations."""

    def __init__(self, engine_factory: EngineFactory) -> None:
        self._engine_factory = engine_factory

    async def _require_engine(self) -> AsyncEngine:
        engine = await self._engine_factory()
        if engine is None:
            raise HomeConfigRepositoryError("home_config_engine_unavailable")
        return engine

    async def get_by_id(self, config_id: uuid.UUID) -> HomeConfig | None:
        engine = await self._require_engine()
        async with engine.connect() as conn:
            result = await conn.execute(
                sa.select(PRODUCT_HOME_CONFIGS_TABLE)
                .where(PRODUCT_HOME_CONFIGS_TABLE.c.id == config_id)
                .limit(1)
            )
            row = result.mappings().first()
        if not row:
            return None
        return self._row_to_config(row)

    async def get_active(self, slug: str) -> HomeConfig | None:
        engine = await self._require_engine()
        async with engine.connect() as conn:
            result = await conn.execute(
                sa.select(PRODUCT_HOME_CONFIGS_TABLE)
                .where(PRODUCT_HOME_CONFIGS_TABLE.c.slug == slug)
                .where(
                    PRODUCT_HOME_CONFIGS_TABLE.c.status
                    == HomeConfigStatus.PUBLISHED.value
                )
                .order_by(
                    PRODUCT_HOME_CONFIGS_TABLE.c.version.desc(),
                    PRODUCT_HOME_CONFIGS_TABLE.c.updated_at.desc(),
                )
                .limit(1)
            )
            row = result.mappings().first()
        if not row:
            return None
        return self._row_to_config(row)

    async def get_draft(self, slug: str) -> HomeConfig | None:
        engine = await self._require_engine()
        async with engine.connect() as conn:
            result = await conn.execute(
                sa.select(PRODUCT_HOME_CONFIGS_TABLE)
                .where(PRODUCT_HOME_CONFIGS_TABLE.c.slug == slug)
                .where(
                    PRODUCT_HOME_CONFIGS_TABLE.c.status == HomeConfigStatus.DRAFT.value
                )
                .order_by(PRODUCT_HOME_CONFIGS_TABLE.c.updated_at.desc())
                .limit(1)
            )
            row = result.mappings().first()
        if not row:
            return None
        return self._row_to_config(row)

    async def create_draft(
        self,
        slug: str,
        data: Mapping[str, Any],
        *,
        actor: str | None,
        base_config_id: uuid.UUID | None,
    ) -> HomeConfig:
        engine = await self._require_engine()
        now = _utcnow()
        async with engine.begin() as conn:
            max_version = await self._max_version(conn, slug)
            stmt = (
                PRODUCT_HOME_CONFIGS_TABLE.insert()
                .values(
                    id=uuid.uuid4(),
                    slug=slug,
                    version=max_version,
                    status=HomeConfigStatus.DRAFT.value,
                    data=dict(data),
                    created_by=actor,
                    updated_by=actor,
                    created_at=now,
                    updated_at=now,
                    draft_of=base_config_id,
                )
                .returning(PRODUCT_HOME_CONFIGS_TABLE)
            )
            row = (await conn.execute(stmt)).mappings().one()
        return self._row_to_config(row)

    async def update_draft(
        self,
        config_id: uuid.UUID,
        data: Mapping[str, Any],
        *,
        actor: str | None,
    ) -> HomeConfig:
        engine = await self._require_engine()
        now = _utcnow()
        async with engine.begin() as conn:
            stmt = (
                PRODUCT_HOME_CONFIGS_TABLE.update()
                .where(PRODUCT_HOME_CONFIGS_TABLE.c.id == config_id)
                .where(
                    PRODUCT_HOME_CONFIGS_TABLE.c.status == HomeConfigStatus.DRAFT.value
                )
                .values(
                    data=dict(data),
                    updated_by=actor,
                    updated_at=now,
                )
                .returning(PRODUCT_HOME_CONFIGS_TABLE)
            )
            result = await conn.execute(stmt)
            row = result.mappings().first()
            if row is None:
                raise HomeConfigDraftNotFound("home_config_draft_not_found")
        return self._row_to_config(row)

    async def publish(
        self,
        config_id: uuid.UUID,
        *,
        actor: str | None,
    ) -> HomeConfig:
        engine = await self._require_engine()
        now = _utcnow()
        async with engine.begin() as conn:
            current_row = (
                (
                    await conn.execute(
                        sa.select(PRODUCT_HOME_CONFIGS_TABLE)
                        .where(PRODUCT_HOME_CONFIGS_TABLE.c.id == config_id)
                        .with_for_update()
                    )
                )
                .mappings()
                .first()
            )
            if current_row is None:
                raise HomeConfigDraftNotFound("home_config_draft_not_found")
            if current_row["status"] != HomeConfigStatus.DRAFT.value:
                raise HomeConfigRepositoryError("config_not_in_draft_state")
            slug = str(current_row["slug"])
            max_version = await self._max_version(conn, slug)
            new_version = max_version + 1
            stmt = (
                PRODUCT_HOME_CONFIGS_TABLE.update()
                .where(PRODUCT_HOME_CONFIGS_TABLE.c.id == config_id)
                .values(
                    status=HomeConfigStatus.PUBLISHED.value,
                    version=new_version,
                    updated_by=actor,
                    updated_at=now,
                    published_at=now,
                )
                .returning(PRODUCT_HOME_CONFIGS_TABLE)
            )
            row = (await conn.execute(stmt)).mappings().one()
        return self._row_to_config(row)

    async def restore_version(
        self,
        slug: str,
        version: int,
        *,
        actor: str | None,
    ) -> HomeConfig:
        engine = await self._require_engine()
        now = _utcnow()
        async with engine.begin() as conn:
            source = (
                (
                    await conn.execute(
                        sa.select(PRODUCT_HOME_CONFIGS_TABLE)
                        .where(PRODUCT_HOME_CONFIGS_TABLE.c.slug == slug)
                        .where(
                            PRODUCT_HOME_CONFIGS_TABLE.c.version == version,
                            PRODUCT_HOME_CONFIGS_TABLE.c.status
                            == HomeConfigStatus.PUBLISHED.value,
                        )
                        .order_by(PRODUCT_HOME_CONFIGS_TABLE.c.updated_at.desc())
                        .limit(1)
                    )
                )
                .mappings()
                .first()
            )
            if source is None:
                raise HomeConfigNotFound("home_config_version_not_found")
            stmt = (
                PRODUCT_HOME_CONFIGS_TABLE.insert()
                .values(
                    id=uuid.uuid4(),
                    slug=slug,
                    version=source["version"],
                    status=HomeConfigStatus.DRAFT.value,
                    data=_as_mapping(source.get("data")),
                    created_by=actor,
                    updated_by=actor,
                    created_at=now,
                    updated_at=now,
                    draft_of=_as_uuid(source["id"]),
                )
                .returning(PRODUCT_HOME_CONFIGS_TABLE)
            )
            row = (await conn.execute(stmt)).mappings().one()
        return self._row_to_config(row)

    async def add_audit(
        self,
        *,
        config_id: uuid.UUID,
        version: int,
        action: str,
        actor: str | None,
        actor_team: str | None,
        comment: str | None,
        data: Mapping[str, Any] | None,
        diff: list[dict[str, Any]] | None,
    ) -> HomeConfigAudit:
        engine = await self._require_engine()
        now = _utcnow()
        payload = dict(data) if data is not None else None
        diff_payload = None
        if diff is not None:
            diff_payload = [dict(item) for item in diff]
        async with engine.begin() as conn:
            stmt = (
                HOME_CONFIG_AUDITS_TABLE.insert()
                .values(
                    id=uuid.uuid4(),
                    config_id=config_id,
                    version=version,
                    action=action,
                    actor=actor,
                    actor_team=actor_team,
                    comment=comment,
                    data=payload,
                    diff=diff_payload,
                    created_at=now,
                )
                .returning(HOME_CONFIG_AUDITS_TABLE)
            )
            row = (await conn.execute(stmt)).mappings().one()
        return self._row_to_audit(row)

    async def list_history(
        self,
        slug: str,
        *,
        limit: int = 20,
    ) -> list[HomeConfigHistoryEntry]:
        engine = await self._require_engine()
        async with engine.connect() as conn:
            result = await conn.execute(
                sa.select(PRODUCT_HOME_CONFIGS_TABLE)
                .where(PRODUCT_HOME_CONFIGS_TABLE.c.slug == slug)
                .where(
                    PRODUCT_HOME_CONFIGS_TABLE.c.status
                    == HomeConfigStatus.PUBLISHED.value
                )
                .order_by(
                    PRODUCT_HOME_CONFIGS_TABLE.c.version.desc(),
                    PRODUCT_HOME_CONFIGS_TABLE.c.published_at.desc(),
                    PRODUCT_HOME_CONFIGS_TABLE.c.updated_at.desc(),
                )
                .limit(limit)
            )
            config_rows = result.mappings().all()
            if not config_rows:
                return []
            config_ids = [row["id"] for row in config_rows]
            audit_rows = (
                (
                    await conn.execute(
                        sa.select(HOME_CONFIG_AUDITS_TABLE)
                        .where(HOME_CONFIG_AUDITS_TABLE.c.config_id.in_(config_ids))
                        .where(HOME_CONFIG_AUDITS_TABLE.c.action == "publish")
                        .order_by(
                            HOME_CONFIG_AUDITS_TABLE.c.config_id,
                            HOME_CONFIG_AUDITS_TABLE.c.created_at.desc(),
                        )
                    )
                )
                .mappings()
                .all()
            )
        audits_by_config: dict[uuid.UUID, HomeConfigAudit] = {}
        for audit_row in audit_rows:
            config_id = _as_uuid(audit_row["config_id"])
            if config_id not in audits_by_config:
                audits_by_config[config_id] = self._row_to_audit(audit_row)
        entries: list[HomeConfigHistoryEntry] = []
        for row in config_rows:
            config = self._row_to_config(row)
            audit = audits_by_config.get(config.id)
            fallback_created = (
                config.published_at or config.updated_at or config.created_at
            )
            created_at = audit.created_at if audit else fallback_created
            entries.append(
                HomeConfigHistoryEntry(
                    config=config,
                    actor=audit.actor if audit else config.updated_by,
                    actor_team=audit.actor_team if audit else None,
                    comment=audit.comment if audit else None,
                    created_at=created_at,
                    diff=audit.diff if audit else None,
                )
            )
        return entries

    async def _max_version(self, conn: AsyncConnection, slug: str) -> int:
        result = await conn.execute(
            sa.select(
                sa.func.coalesce(sa.func.max(PRODUCT_HOME_CONFIGS_TABLE.c.version), 0)
            ).where(PRODUCT_HOME_CONFIGS_TABLE.c.slug == slug)
        )
        value = result.scalar_one()
        return int(value or 0)

    def _row_to_config(self, row: Mapping[str, Any]) -> HomeConfig:
        status_value = row.get("status")
        if isinstance(status_value, HomeConfigStatus):
            status = status_value
        else:
            status = HomeConfigStatus(str(status_value))
        return HomeConfig(
            id=_as_uuid(row["id"]),
            slug=str(row["slug"]),
            version=int(row.get("version") or 0),
            status=status,
            data=_as_mapping(row.get("data")),
            created_by=row.get("created_by"),
            updated_by=row.get("updated_by"),
            created_at=_as_datetime(row.get("created_at")),
            updated_at=_as_datetime(row.get("updated_at")),
            published_at=(
                None
                if row.get("published_at") is None
                else _as_datetime(row.get("published_at"))
            ),
            draft_of=(
                None if row.get("draft_of") is None else _as_uuid(row.get("draft_of"))
            ),
        )

    def _row_to_audit(self, row: Mapping[str, Any]) -> HomeConfigAudit:
        actor_value = row.get("actor")
        actor_team_value = row.get("actor_team")
        return HomeConfigAudit(
            id=_as_uuid(row["id"]),
            config_id=_as_uuid(row["config_id"]),
            version=int(row.get("version") or 0),
            action=str(row.get("action")),
            actor=str(actor_value) if actor_value is not None else None,
            actor_team=(
                str(actor_team_value) if actor_team_value not in (None, "") else None
            ),
            comment=(
                str(row.get("comment"))
                if row.get("comment") not in (None, "")
                else None
            ),
            data=_as_mapping(row.get("data")) if row.get("data") is not None else None,
            diff=_as_patch(row.get("diff")),
            created_at=_as_datetime(row.get("created_at")),
        )


__all__ = ["HomeConfigRepository", "EngineFactory"]
