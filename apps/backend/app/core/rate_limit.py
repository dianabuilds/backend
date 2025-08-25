from __future__ import annotations

import re
import time
from collections import deque
from datetime import datetime
from typing import Optional

import redis.asyncio as redis
from fastapi import Depends, Request, Response
from fastapi.responses import JSONResponse
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.policy import policy
from app.core.real_ip import get_real_ip
from app.core.redis_utils import create_async_redis


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
        ip = get_real_ip(request)
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
    """
    Новая версия: принимает "ключ" правила (login, login_json, signup, evm_nonce, evm_verify, change_password)
    и читает актуальное значение из настроек на каждом запросе.
    """
    attr = f"rules_{key}"

    async def _callback(request: Request, response: Response, pexpire):  # pragma: no cover
        ip = get_real_ip(request)
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
        if (
            not settings.rate_limit.enabled
            or policy.rate_limit_mode != "enforce"
            or request.method.upper() == "OPTIONS"
            or request.url.path in {"/health", "/readiness"}
        ):
            return
        rule_str = getattr(settings.rate_limit, attr, None)
        if not rule_str:
            return  # правило не настроено — пропускаем
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
    redis_url = settings.rate_limit.redis_url
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


# --- Token bucket middleware -------------------------------------------------

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
    """Token-bucket rate limiting using Redis.

    The key has the format ``rl:{workspace_id}:{user_id}:{operation}``.
    When the limit is exceeded the middleware sets the ``Retry-After`` header
    and returns ``429``.
    """

    def __init__(
        self,
        app,
        *,
        capacity: int,
        fill_rate: float,
        burst: int,
        redis_client: Optional[redis.Redis] = None,
        redis_url: str | None = None,
    ) -> None:
        super().__init__(app)
        self.capacity = capacity
        self.fill_rate = fill_rate
        self.burst = burst
        if redis_client is not None:
            self._redis = redis_client
        else:
            redis_url = redis_url or settings.rate_limit.redis_url
            self._redis = create_async_redis(
                redis_url, decode_responses=True, connect_timeout=2.0, max_connections=100
            )

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        if policy.rate_limit_mode != "enforce":
            return await call_next(request)
        workspace_id = request.headers.get("X-Workspace-ID", "0")
        user_id = request.headers.get("X-User-ID", "0")
        operation = request.headers.get("X-Operation", request.url.path)
        allowed, retry_after = await self._acquire(workspace_id, user_id, operation)
        if allowed:
            return await call_next(request)
        response = Response(status_code=429)
        if retry_after > 0:
            response.headers["Retry-After"] = str(int(retry_after))
        return response

    async def _acquire(
        self, workspace_id: str, user_id: str, operation: str
    ) -> tuple[bool, float]:
        key = f"rl:{workspace_id}:{user_id}:{operation}"
        now = time.time()
        try:
            allowed, retry = await self._redis.eval(
                TOKEN_BUCKET_SCRIPT,
                1,
                key,
                self.capacity,
                self.fill_rate,
                self.burst,
                now,
            )
            return bool(int(allowed)), float(retry)
        except Exception:  # pragma: no cover - fallback for minimal redis
            data = await self._redis.hgetall(key) or {}
            tokens = float(data.get("tokens", self.capacity + self.burst))
            timestamp = float(data.get("timestamp", now))
            delta = now - timestamp
            max_tokens = self.capacity + self.burst
            tokens = min(tokens + delta * self.fill_rate, max_tokens)
            if tokens >= 1:
                tokens -= 1
                allowed = True
                retry = 0.0
            else:
                allowed = False
                retry = (1 - tokens) / self.fill_rate
            await self._redis.hset(
                key, mapping={"tokens": tokens, "timestamp": now}
            )
            await self._redis.expire(
                key, int(max_tokens / self.fill_rate) or 1
            )
            return allowed, retry
