from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Annotated, Any
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache as shared_cache
from app.core.config import settings
from app.core.redis_utils import create_async_redis
from app.domains.ai.application.embedding_service import get_embedding
from app.providers.db.session import get_db

try:
    import redis.asyncio as redis  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    redis = None

logger = logging.getLogger(__name__)

router = APIRouter()


READYZ_CACHE_TTL = 5


@router.get("/health", include_in_schema=False)
@router.get("/healthz", include_in_schema=False)
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/startupz", include_in_schema=False)
async def startupz() -> dict[str, str]:
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
        client = create_async_redis(url, decode_responses=True, connect_timeout=2.0)
        await client.ping()
        return True
    except Exception as exc:
        status = getattr(
            getattr(exc, "response", None),
            "status_code",
            getattr(exc, "status_code", None),
        )
        if status:
            logger.exception("redis_check_failed status=%s", status)
        else:
            logger.exception("redis_check_failed")
        return False


async def _check_queue() -> bool:
    if not (settings.async_enabled and settings.queue_broker_url):
        return True
    try:
        parsed = urlparse(settings.queue_broker_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or (5672 if parsed.scheme.startswith("amqp") else 0)
        reader, writer = await asyncio.open_connection(host, port)
        writer.close()
        await writer.wait_closed()
        return True
    except Exception as exc:
        status = getattr(
            getattr(exc, "response", None),
            "status_code",
            getattr(exc, "status_code", None),
        )
        if status:
            logger.exception("queue_check_failed status=%s", status)
        else:
            logger.exception("queue_check_failed")
        return False


async def _check_ai_service(timeout: float) -> bool:
    # Проверяем фактическую работоспособность провайдера эмбеддингов.
    # Важно: get_embedding использует синхронные HTTP-клиенты, поэтому
    # переносим выполнение в отдельный поток, чтобы не блокировать event loop.
    try:
        vec = await asyncio.to_thread(get_embedding, "health check")
        return isinstance(vec, list) and len(vec) > 0
    except Exception as exc:
        status = getattr(
            getattr(exc, "response", None),
            "status_code",
            getattr(exc, "status_code", None),
        )
        if status:
            logger.exception("ai_service_check_failed status=%s", status)
        else:
            logger.exception("ai_service_check_failed")
        return False


async def _check_payment_service(timeout: float) -> bool:
    base = settings.payment.api_base
    if not base:
        return True
    url = base.rstrip("/") + "/health"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url)
            if 200 <= resp.status_code < 300:
                return True
            logger.warning("payment_health_failed status=%s", resp.status_code)
            return False
    except Exception:
        return False


@router.get("/readyz", include_in_schema=False)
async def readyz(db: Annotated[AsyncSession, Depends(get_db)]) -> JSONResponse:
    cache_key = "ops:readyz"
    cached = await shared_cache.get(cache_key)
    if cached:
        data = json.loads(cached)
        return JSONResponse(status_code=data["status"], content=data["body"])

    obs = settings.observability
    db_timeout = obs.db_check_timeout_ms / 1000
    redis_timeout = obs.redis_check_timeout_ms / 1000
    queue_timeout = obs.queue_check_timeout_ms / 1000
    ai_timeout = obs.ai_check_timeout_ms / 1000
    payment_timeout = obs.payment_check_timeout_ms / 1000

    async def db_check() -> bool:
        return await _check_db(db)

    async def redis_check() -> bool:
        return await _check_redis()

    async def queue_check() -> bool:
        return await _check_queue()

    async def ai_check() -> bool:
        return await _check_ai_service(ai_timeout)

    async def payment_check() -> bool:
        return await _check_payment_service(payment_timeout)

    start = time.perf_counter()
    tasks = {
        "db": asyncio.wait_for(db_check(), db_timeout),
        "redis": asyncio.wait_for(redis_check(), redis_timeout),
        "queue": asyncio.wait_for(queue_check(), queue_timeout),
        "ai": asyncio.wait_for(ai_check(), ai_timeout),
        "payment": asyncio.wait_for(payment_check(), payment_timeout),
    }
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    duration_ms = int((time.perf_counter() - start) * 1000)

    result: dict[str, Any] = {"duration_ms": duration_ms}
    status = 200
    for name, value in zip(tasks.keys(), results, strict=False):
        ok = value is True
        result[name] = "ok" if ok else "fail"
        if not ok:
            status = 503
            logger.warning("%s_check_failed %r", name, value)

    payload = {"status": status, "body": result}
    await shared_cache.set(cache_key, json.dumps(payload), READYZ_CACHE_TTL)
    return JSONResponse(status_code=status, content=result)
