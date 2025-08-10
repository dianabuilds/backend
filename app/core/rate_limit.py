from __future__ import annotations

import re

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


def rate_limit_dep(rule: str):
    times, seconds = _parse_rule(rule)

    async def _callback(request: Request, response: Response, pexpire):  # pragma: no cover
        return JSONResponse({"detail": "rate limit exceeded"}, status_code=429)

    async def _dep(request: Request, response: Response):
        if not settings.rate_limit.enabled:
            return
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
