from __future__ import annotations

import logging
from functools import lru_cache

from fastapi import Depends, Header, Request, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from packages.core.config import to_async_dsn
from packages.core.db import get_async_engine
from packages.core.errors import ApiError

from .routers import get_container

logger = logging.getLogger(__name__)

IDEMPOTENCY_HEADER = "Idempotency-Key"
IDEMPOTENCY_RETRY_SECONDS = 5


@lru_cache(maxsize=1)
def _engine_for_dsn(dsn: str) -> AsyncEngine:
    return get_async_engine("idempotency", url=dsn, pool_pre_ping=True, future=True)


class IdempotencyStore:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def reserve(self, key: str) -> bool:
        stmt = text(
            """
            INSERT INTO idempotency_keys(key, locked, created_at)
            VALUES (:key, true, now())
            ON CONFLICT (key) DO NOTHING
            """
        )
        async with self._engine.begin() as conn:
            result = await conn.execute(stmt, {"key": key})
        return bool(getattr(result, "rowcount", 0))


def _get_store(settings) -> IdempotencyStore | None:
    try:
        dsn = to_async_dsn(settings.database_url)
    except Exception as exc:
        logger.exception("Failed to derive DSN for idempotency storage", exc_info=exc)
        return None
    if not dsn:
        return None
    engine = _engine_for_dsn(str(dsn))
    return IdempotencyStore(engine)


async def require_idempotency_key(
    request: Request,
    key: str | None = Header(
        default=None, alias=IDEMPOTENCY_HEADER, convert_underscores=False
    ),
    container=Depends(get_container),
) -> str:
    if not key:
        raise ApiError(
            code="E_IDEMPOTENCY_KEY_REQUIRED",
            status_code=status.HTTP_400_BAD_REQUEST,
            message=f"{IDEMPOTENCY_HEADER} header required",
        )
    store = _get_store(container.settings)
    if store is None:
        raise ApiError(
            code="E_IDEMPOTENCY_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message="Idempotency storage unavailable",
        )
    inserted = await store.reserve(key)
    if not inserted:
        raise ApiError(
            code="E_IDEMPOTENCY_CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            message="Request already processed",
            retry_after=IDEMPOTENCY_RETRY_SECONDS,
        )
    request.state.idempotency_key = key
    return key


__all__ = [
    "IDEMPOTENCY_HEADER",
    "IDEMPOTENCY_RETRY_SECONDS",
    "require_idempotency_key",
    "IdempotencyStore",
]
