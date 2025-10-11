from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.product.worlds.application.ports import Repo
from domains.product.worlds.domain.entities import Character, WorldTemplate
from packages.core.async_utils import run_sync
from packages.core.config import sanitize_async_dsn
from packages.core.db import get_async_engine
from packages.core.sql_fallback import evaluate_sql_backend

from ..memory.repository import MemoryRepo

logger = logging.getLogger(__name__)


class SQLWorldsRepo(Repo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        if isinstance(engine, str):
            self._engine: AsyncEngine | None = None
            self._dsn: str | None = sanitize_async_dsn(engine)
        else:
            self._engine = engine
            self._dsn = None

    def _engine_for_call(self) -> tuple[AsyncEngine, bool]:
        if self._engine is not None:
            return self._engine, False
        if self._dsn is None:
            raise RuntimeError("SQLWorldsRepo requires an engine or DSN configuration")
        return get_async_engine("worlds", url=self._dsn), True

    # --- Worlds ---
    def list_worlds(self) -> list[WorldTemplate]:
        async def _run() -> list[WorldTemplate]:
            sql = text(
                """
                SELECT id::text AS id,
                       title, locale, description, meta,
                       created_at, updated_at,
                       created_by_user_id::text AS created_by_user_id,
                       updated_by_user_id::text AS updated_by_user_id
                  FROM worlds
                 ORDER BY created_at DESC
                """
            )
            engine, dispose = self._engine_for_call()
            try:
                async with engine.begin() as conn:
                    rows = (await conn.execute(sql)).mappings().all()
                return [
                    WorldTemplate(
                        id=str(row["id"]),
                        title=str(row["title"]),
                        locale=row["locale"],
                        description=row["description"],
                        meta=row["meta"] or {},
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                        created_by_user_id=row.get("created_by_user_id"),
                        updated_by_user_id=row.get("updated_by_user_id"),
                    )
                    for row in rows
                ]
            finally:
                if dispose:
                    await engine.dispose()

        return self._run_sync(_run())

    def get_world(self, world_id: str) -> WorldTemplate | None:
        async def _run() -> WorldTemplate | None:
            sql = text(
                """
                SELECT id::text AS id,
                       title, locale, description, meta,
                       created_at, updated_at,
                       created_by_user_id::text AS created_by_user_id,
                       updated_by_user_id::text AS updated_by_user_id
                  FROM worlds
                 WHERE id = cast(:id as uuid)
                """
            )
            engine, dispose = self._engine_for_call()
            try:
                async with engine.begin() as conn:
                    row = (await conn.execute(sql, {"id": world_id})).mappings().first()
                if not row:
                    return None
                return WorldTemplate(
                    id=str(row["id"]),
                    title=str(row["title"]),
                    locale=row["locale"],
                    description=row["description"],
                    meta=row["meta"] or {},
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    created_by_user_id=row.get("created_by_user_id"),
                    updated_by_user_id=row.get("updated_by_user_id"),
                )
            finally:
                if dispose:
                    await engine.dispose()

        return self._run_sync(_run())

    def create_world(self, data: dict, actor_id: str) -> WorldTemplate:
        async def _run() -> WorldTemplate:
            sql = text(
                """
                INSERT INTO worlds(
                    title, locale, description, meta,
                    created_by_user_id, updated_by_user_id
                )
                VALUES (
                    :title, :locale, :description, cast(:meta as jsonb),
                    cast(:actor as uuid), cast(:actor as uuid)
                )
                RETURNING id::text AS id,
                          title, locale, description, meta,
                          created_at, updated_at,
                          created_by_user_id::text AS created_by_user_id,
                          updated_by_user_id::text AS updated_by_user_id
                """
            )
            params: dict[str, Any] = {
                "title": str(data.get("title") or "").strip(),
                "locale": data.get("locale"),
                "description": str(data.get("description") or "").strip(),
                "meta": json.dumps(data.get("meta") or {}),
                "actor": actor_id,
            }
            engine, dispose = self._engine_for_call()
            try:
                async with engine.begin() as conn:
                    row = (await conn.execute(sql, params)).mappings().first()
                if row is None:

                    raise RuntimeError("database_row_missing")
                return WorldTemplate(
                    id=str(row["id"]),
                    title=str(row["title"]),
                    locale=row["locale"],
                    description=row["description"],
                    meta=row["meta"] or {},
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    created_by_user_id=row.get("created_by_user_id"),
                    updated_by_user_id=row.get("updated_by_user_id"),
                )
            finally:
                if dispose:
                    await engine.dispose()

        return self._run_sync(_run())

    def update_world(
        self, world: WorldTemplate, data: dict, actor_id: str
    ) -> WorldTemplate:
        async def _run() -> WorldTemplate:
            sets = [
                "updated_at = now()",
                "updated_by_user_id = cast(:actor as uuid)",
            ]
            params: dict[str, Any] = {"id": world.id, "actor": actor_id}
            if "title" in data and data["title"] is not None:
                sets.append("title = :title")
                params["title"] = str(data["title"]).strip()
            if "locale" in data:
                sets.append("locale = :locale")
                params["locale"] = data.get("locale")
            if "description" in data:
                sets.append("description = :description")
                params["description"] = str(data.get("description") or "").strip()
            if "meta" in data and data["meta"] is not None:
                sets.append("meta = cast(:meta as jsonb)")
                params["meta"] = json.dumps(dict(data["meta"]) or {})
            sql = text(
                """
                UPDATE worlds
                   SET """
                + ", ".join(sets)
                + " WHERE id = cast(:id as uuid)"
                + " RETURNING id::text AS id, title, locale, description, meta, created_at, updated_at, created_by_user_id::text AS created_by_user_id, updated_by_user_id::text AS updated_by_user_id"
            )
            engine, dispose = self._engine_for_call()
            try:
                async with engine.begin() as conn:
                    row = (await conn.execute(sql, params)).mappings().first()
                if not row:
                    return world
                return WorldTemplate(
                    id=str(row["id"]),
                    title=str(row["title"]),
                    locale=row["locale"],
                    description=row["description"],
                    meta=row["meta"] or {},
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    created_by_user_id=row.get("created_by_user_id"),
                    updated_by_user_id=row.get("updated_by_user_id"),
                )
            finally:
                if dispose:
                    await engine.dispose()

        return self._run_sync(_run())

    def delete_world(self, world: WorldTemplate) -> None:
        async def _run() -> None:
            sql = text("DELETE FROM worlds WHERE id = cast(:id as uuid)")
            engine, dispose = self._engine_for_call()
            try:
                async with engine.begin() as conn:
                    await conn.execute(sql, {"id": world.id})
            finally:
                if dispose:
                    await engine.dispose()

        self._run_sync(_run())

    # --- Characters ---
    def list_characters(self, world_id: str) -> list[Character]:
        async def _run() -> list[Character]:
            sql = text(
                """
                SELECT id::text AS id,
                       world_id::text AS world_id,
                       name, role, description, traits,
                       created_at, updated_at,
                       created_by_user_id::text AS created_by_user_id,
                       updated_by_user_id::text AS updated_by_user_id
                  FROM world_characters
                 WHERE world_id = cast(:world_id as uuid)
                 ORDER BY created_at DESC
                """
            )
            engine, dispose = self._engine_for_call()
            try:
                async with engine.begin() as conn:
                    rows = (
                        (await conn.execute(sql, {"world_id": world_id}))
                        .mappings()
                        .all()
                    )
                return [
                    Character(
                        id=str(row["id"]),
                        world_id=str(row["world_id"]),
                        name=str(row["name"]),
                        role=row["role"],
                        description=row["description"],
                        traits=row["traits"] or {},
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                        created_by_user_id=row.get("created_by_user_id"),
                        updated_by_user_id=row.get("updated_by_user_id"),
                    )
                    for row in rows
                ]
            finally:
                if dispose:
                    await engine.dispose()

        return self._run_sync(_run())

    def get_character(self, char_id: str) -> Character | None:
        async def _run() -> Character | None:
            sql = text(
                """
                SELECT id::text AS id,
                       world_id::text AS world_id,
                       name, role, description, traits,
                       created_at, updated_at,
                       created_by_user_id::text AS created_by_user_id,
                       updated_by_user_id::text AS updated_by_user_id
                  FROM world_characters
                 WHERE id = cast(:id as uuid)
                """
            )
            engine, dispose = self._engine_for_call()
            try:
                async with engine.begin() as conn:
                    row = (await conn.execute(sql, {"id": char_id})).mappings().first()
                if not row:
                    return None
                return Character(
                    id=str(row["id"]),
                    world_id=str(row["world_id"]),
                    name=str(row["name"]),
                    role=row["role"],
                    description=row["description"],
                    traits=row["traits"] or {},
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    created_by_user_id=row.get("created_by_user_id"),
                    updated_by_user_id=row.get("updated_by_user_id"),
                )
            finally:
                if dispose:
                    await engine.dispose()

        return self._run_sync(_run())

    def create_character(self, world_id: str, data: dict, actor_id: str) -> Character:
        async def _run() -> Character:
            ensure_sql = text("SELECT 1 FROM worlds WHERE id = cast(:id as uuid)")
            insert_sql = text(
                """
                INSERT INTO world_characters(
                    world_id, name, role, description, traits,
                    created_by_user_id, updated_by_user_id
                )
                VALUES (
                    cast(:world_id as uuid), :name, :role, :description, cast(:traits as jsonb),
                    cast(:actor as uuid), cast(:actor as uuid)
                )
                RETURNING id::text AS id,
                          world_id::text AS world_id,
                          name, role, description, traits,
                          created_at, updated_at,
                          created_by_user_id::text AS created_by_user_id,
                          updated_by_user_id::text AS updated_by_user_id
                """
            )
            params: dict[str, Any] = {
                "world_id": world_id,
                "name": str(data.get("name") or "").strip(),
                "role": data.get("role"),
                "description": str(data.get("description") or "").strip(),
                "traits": json.dumps(data.get("traits") or {}),
                "actor": actor_id,
            }
            engine, dispose = self._engine_for_call()
            try:
                async with engine.begin() as conn:
                    exists = (await conn.execute(ensure_sql, {"id": world_id})).first()
                    if not exists:
                        raise ValueError("world_not_found")
                    row = (await conn.execute(insert_sql, params)).mappings().first()
                if row is None:

                    raise RuntimeError("database_row_missing")
                return Character(
                    id=str(row["id"]),
                    world_id=str(row["world_id"]),
                    name=str(row["name"]),
                    role=row["role"],
                    description=row["description"],
                    traits=row["traits"] or {},
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    created_by_user_id=row.get("created_by_user_id"),
                    updated_by_user_id=row.get("updated_by_user_id"),
                )
            finally:
                if dispose:
                    await engine.dispose()

        return self._run_sync(_run())

    def update_character(self, ch: Character, data: dict, actor_id: str) -> Character:
        async def _run() -> Character:
            sets = [
                "updated_at = now()",
                "updated_by_user_id = cast(:actor as uuid)",
            ]
            params: dict[str, Any] = {"id": ch.id, "actor": actor_id}
            if "name" in data and data["name"] is not None:
                sets.append("name = :name")
                params["name"] = str(data["name"]).strip()
            if "role" in data:
                sets.append("role = :role")
                params["role"] = data.get("role")
            if "description" in data:
                sets.append("description = :description")
                params["description"] = str(data.get("description") or "").strip()
            if "traits" in data and data["traits"] is not None:
                sets.append("traits = cast(:traits as jsonb)")
                params["traits"] = json.dumps(dict(data["traits"]) or {})
            sql = text(
                """
                UPDATE world_characters
                   SET """
                + ", ".join(sets)
                + " WHERE id = cast(:id as uuid)"
                + " RETURNING id::text AS id, world_id::text AS world_id, name, role, description, traits, created_at, updated_at, created_by_user_id::text AS created_by_user_id, updated_by_user_id::text AS updated_by_user_id"
            )
            engine, dispose = self._engine_for_call()
            try:
                async with engine.begin() as conn:
                    row = (await conn.execute(sql, params)).mappings().first()
                if not row:
                    return ch
                return Character(
                    id=str(row["id"]),
                    world_id=str(row["world_id"]),
                    name=str(row["name"]),
                    role=row["role"],
                    description=row["description"],
                    traits=row["traits"] or {},
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    created_by_user_id=row.get("created_by_user_id"),
                    updated_by_user_id=row.get("updated_by_user_id"),
                )
            finally:
                if dispose:
                    await engine.dispose()

        return self._run_sync(_run())

    def delete_character(self, ch: Character) -> None:
        async def _run() -> None:
            sql = text("DELETE FROM world_characters WHERE id = cast(:id as uuid)")
            engine, dispose = self._engine_for_call()
            try:
                async with engine.begin() as conn:
                    await conn.execute(sql, {"id": ch.id})
            finally:
                if dispose:
                    await engine.dispose()

        self._run_sync(_run())

    # Helpers
    def _run_sync(self, coro):
        return run_sync(coro)


def _log_fallback(reason: str | None, error: Exception | None = None) -> None:
    if error is not None:
        logger.warning(
            "worlds repo: falling back to memory due to SQL error: %s", error
        )
        return
    if not reason:
        logger.debug("worlds repo: using memory backend")
        return
    level = logging.DEBUG
    lowered = reason.lower()
    if "invalid" in lowered or "empty" in lowered:
        level = logging.WARNING
    elif "not configured" in lowered or "helpers unavailable" in lowered:
        level = logging.INFO
    logger.log(level, "worlds repo: using memory backend (%s)", reason)


def create_repo(settings) -> Repo:
    decision = evaluate_sql_backend(settings)
    if not decision.dsn:
        _log_fallback(decision.reason)
        return MemoryRepo()
    try:
        return SQLWorldsRepo(decision.dsn)
    except Exception as exc:  # pragma: no cover - defensive fallback
        _log_fallback(decision.reason or "engine initialization failed", error=exc)
        return MemoryRepo()


__all__ = [
    "SQLWorldsRepo",
    "create_repo",
]
