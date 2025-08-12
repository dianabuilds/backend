from __future__ import annotations

import re
from collections import deque
from datetime import datetime

from fastapi import Depends, Request, Response
from fastapi.responses import JSONResponse
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

from app.core.config import settings


def _parse_rule(rule: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d+)\/(\d+)?(second|sec|s|minute|min|hour|h)", rule)
    if not match:
        raise ValueError(f"Invalid rate limit rule: {rule}")
    count = int(match.group(1))
    num = int(match.group(2) or 1)
    unit = match.group(3)
    if unit.startswith("s"):
        seconds = num
    elif unit.startswith("m"):
        seconds = 60 * num
    else:
        seconds = 3600 * num
    return count, seconds


recent_429: deque[dict] = deque(maxlen=50)


def rate_limit_dep(rule: str):
    """
    Историческая версия: принимает строку правила и фиксирует её на момент объявления.
    Оставляем для совместимости, но для динамических изменений используйте rate_limit_dep_key.
    """
    times, seconds = _parse_rule(rule)

    async def _callback(request: Request, response: Response, pexpire):  # pragma: no cover
        ip = request.client.host if request.client else None
        recent_429.append(
            {
                "path": request.url.path,
                "ip": ip,
                "rule": rule,
                "ts": datetime.utcnow().isoformat(),
            }
        )
        return JSONResponse({"detail": "rate limit exceeded"}, status_code=429)

    async def _dep(request: Request, response: Response):
        if not settings.rate_limit.enabled:
            return
        limiter = RateLimiter(times=times, seconds=seconds, callback=_callback)
        return await limiter(request, response)

    return Depends(_dep)


def rate_limit_dep_key(key: str):
    """
    Новая версия: принимает "ключ" правила (login, login_json, signup, evm_nonce, evm_verify, change_password)
    и читает актуальное значение из настроек на каждом запросе.
    """
    attr = f"rules_{key}"

    async def _callback(request: Request, response: Response, pexpire):  # pragma: no cover
        ip = request.client.host if request.client else None
        rule_str = getattr(settings.rate_limit, attr, "")
        recent_429.append(
            {
                "path": request.url.path,
                "ip": ip,
                "rule": rule_str,
                "ts": datetime.utcnow().isoformat(),
            }
        )
        return JSONResponse({"detail": "rate limit exceeded"}, status_code=429)

    async def _dep(request: Request, response: Response):
        if not settings.rate_limit.enabled:
            return
        rule_str = getattr(settings.rate_limit, attr, None)
        if not rule_str:
            return  # правило не настроено — пропускаем
        times, seconds = _parse_rule(rule_str)
        limiter = RateLimiter(times=times, seconds=seconds, callback=_callback)
        return await limiter(request, response)

    return Depends(_dep)


async def init_rate_limiter() -> None:
    if not settings.rate_limit.enabled:
        return
    import redis.asyncio as redis

    redis_client = redis.from_url(
        settings.rate_limit.redis_url, encoding="utf-8", decode_responses=True
    )
    await FastAPILimiter.init(redis_client)


async def close_rate_limiter() -> None:
    if not settings.rate_limit.enabled:
        return
    await FastAPILimiter.close()
