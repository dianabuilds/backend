from __future__ import annotations

import re
import time
from collections import deque
from datetime import datetime

import redis.asyncio as redis
from fastapi import Depends, Request, Response
from fastapi.responses import JSONResponse
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from starlette.middleware.base import BaseHTTPMiddleware

from app.kernel.config import settings
from app.kernel.policy import policy
from app.kernel.middlewares.real_ip import get_real_ip
from app.kernel.adapters.redis import create_async_redis


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
    times, seconds = _parse_rule(rule)

    async def _callback(request: Request, response: Response, pexpire):  # pragma: no cover
        ip = get_real_ip(request)
        recent_429.append(
            {"path": request.url.path, "ip": ip, "rule": rule, "ts": datetime.utcnow().isoformat()}
        )
        return JSONResponse({"detail": "rate limit exceeded"}, status_code=429)

    async def _dep(request: Request, response: Response):
        if (
            not settings.rate_limit.enabled
            or policy.rate_limit_mode != "enforce"
            or request.method.upper() == "OPTIONS"
            or request.url.path in {"/health", "/readiness"}
        ):
            return
        ip = get_real_ip(request)
        if ip and request.client:
            request.scope["client"] = (ip, request.client.port)
        limiter = RateLimiter(times=times, seconds=seconds, callback=_callback)
        return await limiter(request, response)

    return Depends(_dep)


def rate_limit_dep_key(key: str):
    attr = f"rules_{key}"

    async def _callback(request: Request, response: Response, pexpire):  # pragma: no cover
        ip = get_real_ip(request)
        rule_str = getattr(settings.rate_limit, attr, "")
        recent_429.append(
            {"path": request.url.path, "ip": ip, "rule": rule_str, "ts": datetime.utcnow().isoformat()}
        )
        return JSONResponse({"detail": "rate limit exceeded"}, status_code=429)

    async def _dep(request: Request, response: Response):
        if (
            not settings.rate_limit.enabled
            or policy.rate_limit_mode != "enforce"
            or request.method.upper() == "OPTIONS"
            or request.url.path in {"/health", "/readiness"}
        ):
            return
        rule_str = getattr(settings.rate_limit, attr, None)
        if not rule_str:
            return
        times, seconds = _parse_rule(rule_str)
        ip = get_real_ip(request)
        if ip and request.client:
            request.scope["client"] = (ip, request.client.port)
        limiter = RateLimiter(times=times, seconds=seconds, callback=_callback)
        return await limiter(request, response)

    return Depends(_dep)


async def init_rate_limiter() -> None:
    if not settings.rate_limit.enabled or policy.rate_limit_mode != "enforce":
        return
    redis_url = settings.redis_url
    if not redis_url:
        return
    redis_client = create_async_redis(
        redis_url, decode_responses=True, connect_timeout=2.0, max_connections=100
    )
    await FastAPILimiter.init(redis_client)


async def close_rate_limiter() -> None:
    if not settings.rate_limit.enabled or policy.rate_limit_mode != "enforce":
        return
    await FastAPILimiter.close()


TOKEN_BUCKET_SCRIPT = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local fill_rate = tonumber(ARGV[2])
local burst = tonumber(ARGV[3])
local now = tonumber(ARGV[4])

local max_tokens = capacity + burst
local data = redis.call('HMGET', key, 'tokens', 'timestamp')
local tokens = tonumber(data[1])
local timestamp = tonumber(data[2])

if tokens == nil then
    tokens = max_tokens
    timestamp = now
else
    local delta = now - timestamp
    tokens = math.min(tokens + delta * fill_rate, max_tokens)
    timestamp = now
end

local allowed = 0
local retry = 0

if tokens >= 1 then
    allowed = 1
    tokens = tokens - 1
else
    retry = math.ceil((1 - tokens) / fill_rate)
end

redis.call('HSET', key, 'tokens', tokens, 'timestamp', timestamp)
redis.call('EXPIRE', key, math.ceil(max_tokens / fill_rate))

return {allowed, retry}
"""


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        capacity: int,
        fill_rate: float,
        burst: int,
        redis_client: redis.Redis | None = None,
        redis_url: str | None = None,
    ) -> None:
        super().__init__(app)
        self.capacity = capacity
        self.fill_rate = fill_rate
        self.burst = burst
        if redis_client is not None:
            self._redis = redis_client
        else:
            redis_url = redis_url or settings.redis_url
            self._redis = create_async_redis(
                redis_url, decode_responses=True, connect_timeout=2.0, max_connections=100
            )

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        if not settings.rate_limit.enabled or policy.rate_limit_mode != "enforce":
            return await call_next(request)
        user_id = request.headers.get("X-User-ID", "0")
        operation = request.headers.get("X-Operation", request.url.path)
        allowed, retry_after = await self._acquire(user_id, operation)
        if allowed:
            return await call_next(request)
        response = Response(status_code=429)
        if retry_after > 0:
            response.headers["Retry-After"] = str(retry_after)
        return response

    async def _acquire(self, user_id: str, operation: str) -> tuple[bool, int]:
        key = f"rl:{user_id}:{operation}"
        now = int(time.time())
        result = await self._redis.eval(
            TOKEN_BUCKET_SCRIPT,
            keys=[key],
            args=[self.capacity, self.fill_rate, self.burst, now],
        )
        allowed, retry = int(result[0]), int(result[1])
        return allowed == 1, retry


__all__ = [
    "RateLimitMiddleware",
    "rate_limit_dep",
    "rate_limit_dep_key",
    "init_rate_limiter",
    "close_rate_limiter",
]
