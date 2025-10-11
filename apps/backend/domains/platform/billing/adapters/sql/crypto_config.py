from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.platform.billing.ports import CryptoConfigRepo
from packages.core.db import get_async_engine

from ..dsn_utils import normalize_async_dsn

logger = logging.getLogger(__name__)


class SQLCryptoConfigRepo(CryptoConfigRepo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        if isinstance(engine, str):
            self._engine = get_async_engine(
                "billing-crypto-config", url=normalize_async_dsn(engine)
            )
        else:
            self._engine = engine

    async def get(self, slug: str) -> dict[str, Any] | None:
        sql = text(
            "SELECT slug, config, updated_at FROM crypto_config WHERE slug=:slug"
        )
        async with self._engine.begin() as conn:
            try:
                r = (await conn.execute(sql, {"slug": slug})).mappings().first()
            except SQLAlchemyError as exc:
                logger.warning("Failed to load crypto config %s: %s", slug, exc)
                return None
            if not r:
                return None
            cfg = dict(r["config"]) if r["config"] is not None else {}
            return {"slug": r["slug"], "config": cfg, "updated_at": r["updated_at"]}

    async def set(self, slug: str, cfg: dict[str, Any]) -> dict[str, Any]:
        sql = text(
            """
            INSERT INTO crypto_config (slug, config, updated_at)
            VALUES (:slug, cast(:config as jsonb), now())
            ON CONFLICT (slug) DO UPDATE SET config = excluded.config, updated_at = now()
            RETURNING slug, config, updated_at
            """
        )
        async with self._engine.begin() as conn:
            r = (
                (await conn.execute(sql, {"slug": slug, "config": cfg}))
                .mappings()
                .first()
            )
            if r is None:

                raise RuntimeError("database_row_missing")
            return {
                "slug": r["slug"],
                "config": dict(r["config"]) if r["config"] is not None else {},
                "updated_at": r["updated_at"],
            }


__all__ = ["SQLCryptoConfigRepo"]
