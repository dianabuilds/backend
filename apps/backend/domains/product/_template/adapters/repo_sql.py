from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from dataclasses import replace

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from packages.core.db import get_async_engine

from ..application.ports import ProductDTO, Repo

logger = logging.getLogger(__name__)

_TABLE_NAME = "product_template_items"


class SQLRepo(Repo):
    """Минимальный рабочий репозиторий для шаблонного домена.

    * Если передать DSN, подключится к Postgres через packages.core.db и создаст
      таблицу "product_template_items" при первом использовании.
    * Если DSN не задан или БД недоступна, хранение идёт в памяти - это позволяет
      скопировать шаблон и сразу запустить домен.
    * Разработчик может постепенно заменять логику SQL/ORM по мере появления
      реальной схемы.
    """

    def __init__(self, dsn: str | None = None) -> None:
        self._dsn = dsn
        self._engine: AsyncEngine | None = None
        self._schema_ready = False
        self._memory: dict[str, ProductDTO] = {}
        self._lock = asyncio.Lock()
        if dsn:
            try:
                self._engine = get_async_engine("product-template", url=dsn)
            except Exception as exc:  # pragma: no cover - fallback path
                logger.warning("Template SQLRepo: fallback to in-memory store: %s", exc)
                self._engine = None

    async def _ensure_schema(self) -> None:
        if self._engine is None or self._schema_ready:
            return
        async with self._engine.begin() as conn:
            await conn.execute(
                text(
                    f"""
                    CREATE TABLE IF NOT EXISTS {_TABLE_NAME} (
                        id text PRIMARY KEY,
                        owner_id text NOT NULL,
                        name text NOT NULL,
                        is_active boolean NOT NULL,
                        created_at timestamptz NOT NULL DEFAULT now(),
                        updated_at timestamptz NOT NULL DEFAULT now()
                    )
                    """
                )
            )
        self._schema_ready = True

    @staticmethod
    def _row_to_dto(row: dict) -> ProductDTO:
        return ProductDTO(
            id=str(row["id"]),
            owner_id=str(row["owner_id"]),
            name=str(row["name"]),
            is_active=bool(row["is_active"]),
        )

    async def get(self, product_id: str) -> ProductDTO | None:  # type: ignore[override]
        if self._engine is None:
            async with self._lock:
                value = self._memory.get(product_id)
                return replace(value) if value else None
        await self._ensure_schema()
        async with self._engine.begin() as conn:
            row = (
                (
                    await conn.execute(
                        text(
                            f"SELECT id, owner_id, name, is_active FROM {_TABLE_NAME} WHERE id = :id"
                        ),
                        {"id": product_id},
                    )
                )
                .mappings()
                .first()
            )
        return None if row is None else self._row_to_dto(row)

    async def list_by_owner(
        self, owner_id: str, *, limit: int = 50, offset: int = 0
    ) -> Sequence[ProductDTO]:  # type: ignore[override]
        if self._engine is None:
            async with self._lock:
                items = [replace(dto) for dto in self._memory.values() if dto.owner_id == owner_id]
            return items[offset : offset + limit]
        await self._ensure_schema()
        async with self._engine.begin() as conn:
            rows = (
                (
                    await conn.execute(
                        text(
                            f"""
                        SELECT id, owner_id, name, is_active
                          FROM {_TABLE_NAME}
                         WHERE owner_id = :owner
                         ORDER BY updated_at DESC
                         LIMIT :limit OFFSET :offset
                        """
                        ),
                        {"owner": owner_id, "limit": limit, "offset": offset},
                    )
                )
                .mappings()
                .all()
            )
        return [self._row_to_dto(row) for row in rows]

    async def upsert(self, product: ProductDTO) -> None:  # type: ignore[override]
        if self._engine is None:
            async with self._lock:
                self._memory[product.id] = replace(product)
            return
        await self._ensure_schema()
        async with self._engine.begin() as conn:
            await conn.execute(
                text(
                    f"""
                    INSERT INTO {_TABLE_NAME} (id, owner_id, name, is_active)
                    VALUES (:id, :owner_id, :name, :is_active)
                    ON CONFLICT (id)
                    DO UPDATE SET
                        owner_id = EXCLUDED.owner_id,
                        name = EXCLUDED.name,
                        is_active = EXCLUDED.is_active,
                        updated_at = now()
                    """
                ),
                {
                    "id": product.id,
                    "owner_id": product.owner_id,
                    "name": product.name,
                    "is_active": product.is_active,
                },
            )

    async def delete(self, product_id: str) -> bool:  # type: ignore[override]
        if self._engine is None:
            async with self._lock:
                return self._memory.pop(product_id, None) is not None
        await self._ensure_schema()
        async with self._engine.begin() as conn:
            result = await conn.execute(
                text(f"DELETE FROM {_TABLE_NAME} WHERE id = :id"), {"id": product_id}
            )
            try:
                affected = result.rowcount  # type: ignore[assignment]
            except Exception:  # pragma: no cover - compatibility branch
                affected = None
        return bool(affected)
