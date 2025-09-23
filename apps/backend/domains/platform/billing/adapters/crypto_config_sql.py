from __future__ import annotations

from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from domains.platform.billing.ports import CryptoConfigRepo


def _normalize_async_dsn(url: str) -> str:
    # Ensure async driver and strip libpq-only params (sslmode)
    out = url
    if out.startswith("postgresql://"):
        out = "postgresql+asyncpg://" + out[len("postgresql://") :]
    try:
        u = urlparse(out)
        q = dict(parse_qsl(u.query, keep_blank_values=True))
        if "sslmode" in q:
            # asyncpg does not accept sslmode in URL; remove it
            q.pop("sslmode", None)
        new_q = urlencode(q)
        out = urlunparse((u.scheme, u.netloc, u.path, u.params, new_q, u.fragment))
    except Exception:
        pass
    return out


class SQLCryptoConfigRepo(CryptoConfigRepo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        if isinstance(engine, str):
            self._engine = create_async_engine(_normalize_async_dsn(engine))
        else:
            self._engine = engine

    async def get(self, slug: str) -> dict[str, Any] | None:
        sql = text("SELECT slug, config, updated_at FROM crypto_config WHERE slug=:slug")
        async with self._engine.begin() as conn:
            try:
                r = (await conn.execute(sql, {"slug": slug})).mappings().first()
            except Exception:
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
            r = (await conn.execute(sql, {"slug": slug, "config": cfg})).mappings().first()
            assert r is not None
            return {
                "slug": r["slug"],
                "config": dict(r["config"]) if r["config"] is not None else {},
                "updated_at": r["updated_at"],
            }


__all__ = ["SQLCryptoConfigRepo"]
