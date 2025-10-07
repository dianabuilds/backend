from __future__ import annotations

from collections.abc import Awaitable
from dataclasses import dataclass
from typing import Any, Protocol

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


class EngineFactory(Protocol):
    def __call__(self) -> Awaitable[AsyncEngine | None]: ...


@dataclass
class SavedViewRecord:
    name: str
    config: dict[str, Any]
    is_default: bool
    updated_at: Any | None


class SavedViewsUnavailable(RuntimeError):
    """Raised when saved views storage is not reachable."""


class SavedViewsRepository:
    def __init__(self, engine_factory: EngineFactory) -> None:
        self._engine_factory = engine_factory

    async def _require_engine(self) -> AsyncEngine:
        engine = await self._engine_factory()
        if engine is None:
            raise SavedViewsUnavailable("nodes_saved_views_engine_unavailable")
        return engine

    async def list_for_user(self, user_id: str) -> list[SavedViewRecord]:
        engine = await self._engine_factory()
        if engine is None:
            return []
        async with engine.begin() as conn:
            rows = (
                (
                    await conn.execute(
                        text(
                            """
                            SELECT name, config, is_default, updated_at
                              FROM product_node_saved_views
                             WHERE user_id = cast(:uid as uuid)
                             ORDER BY is_default DESC, updated_at DESC
                            """
                        ),
                        {"uid": user_id},
                    )
                )
                .mappings()
                .all()
            )
        return [
            SavedViewRecord(
                name=str(row["name"]),
                config=dict(row.get("config") or {}),
                is_default=bool(row.get("is_default", False)),
                updated_at=row.get("updated_at"),
            )
            for row in rows
        ]

    async def upsert(
        self,
        user_id: str,
        *,
        name: str,
        config: dict[str, Any],
        is_default: bool,
    ) -> None:
        engine = await self._require_engine()
        async with engine.begin() as conn:
            if is_default:
                await conn.execute(
                    text(
                        """
                        UPDATE product_node_saved_views
                           SET is_default = false
                         WHERE user_id = cast(:uid as uuid)
                           AND is_default = true
                        """
                    ),
                    {"uid": user_id},
                )
            await conn.execute(
                text(
                    """
                    INSERT INTO product_node_saved_views(user_id, name, config, is_default)
                    VALUES (cast(:uid as uuid), :name, cast(:config as jsonb), :def)
                    ON CONFLICT (user_id, name)
                    DO UPDATE
                       SET config = EXCLUDED.config,
                           is_default = EXCLUDED.is_default,
                           updated_at = now()
                    """
                ),
                {
                    "uid": user_id,
                    "name": name,
                    "config": config,
                    "def": is_default,
                },
            )

    async def delete(self, user_id: str, name: str) -> None:
        engine = await self._require_engine()
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    """
                    DELETE FROM product_node_saved_views
                     WHERE user_id = cast(:uid as uuid)
                       AND name = :name
                    """
                ),
                {"uid": user_id, "name": name},
            )

    async def set_default(self, user_id: str, name: str) -> None:
        engine = await self._require_engine()
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    """
                    UPDATE product_node_saved_views
                       SET is_default = false
                     WHERE user_id = cast(:uid as uuid)
                       AND is_default = true
                    """
                ),
                {"uid": user_id},
            )
            await conn.execute(
                text(
                    """
                    UPDATE product_node_saved_views
                       SET is_default = true,
                           updated_at = now()
                     WHERE user_id = cast(:uid as uuid)
                       AND name = :name
                    """
                ),
                {"uid": user_id, "name": name},
            )
