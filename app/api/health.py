from __future__ import annotations

import asyncio
import time
import logging
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.db.session import get_db

try:
    import redis.asyncio as redis  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    redis = None

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", include_in_schema=False)
@router.get("/healthz", include_in_schema=False)
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


async def _check_db(session: AsyncSession) -> bool:
    try:
        await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def _check_redis() -> bool:
    url = settings.cache.redis_url
    if not url or redis is None:
        return True
    try:
        client = redis.from_url(url)
        await client.ping()
        return True
    except Exception:
        return False


@router.get("/readyz", include_in_schema=False)
async def readyz(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    db_timeout = settings.observability.db_check_timeout_ms / 1000
    redis_timeout = settings.observability.redis_check_timeout_ms / 1000

    async def db_check() -> bool:
        return await _check_db(db)

    async def redis_check() -> bool:
        return await _check_redis()

    start = time.perf_counter()
    db_task = asyncio.wait_for(db_check(), db_timeout)
    redis_task = asyncio.wait_for(redis_check(), redis_timeout)
    db_ok, redis_ok = await asyncio.gather(db_task, redis_task, return_exceptions=True)
    duration_ms = int((time.perf_counter() - start) * 1000)

    result = {
        "db": "ok" if db_ok is True else "fail",
        "redis": "ok" if redis_ok is True else "fail",
        "duration_ms": duration_ms,
    }
    status = 200 if result["db"] == "ok" and result["redis"] == "ok" else 503

    if status != 200:
        logger.warning("readiness_check_failed %s", result)
    return JSONResponse(status_code=status, content=result)
