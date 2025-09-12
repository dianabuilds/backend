from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Optional, Tuple

from app.kernel.cache import AbstractAsyncCache


class MemoryCache(AbstractAsyncCache):
    def __init__(self, default_ttl: Optional[float] = None) -> None:
        self._default_ttl = default_ttl
        self._data: Dict[str, Tuple[Any, Optional[float]]] = {}
        self._lock = asyncio.Lock()

    def _is_expired(self, exp: Optional[float]) -> bool:
        return exp is not None and time.monotonic() >= exp

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            item = self._data.get(key)
            if not item:
                return None
            value, exp = item
            if self._is_expired(exp):
                del self._data[key]
                return None
            return value

    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        exp = None
        if ttl is None:
            ttl = self._default_ttl
        if ttl is not None:
            exp = time.monotonic() + float(ttl)
        async with self._lock:
            self._data[key] = (value, exp)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._data.pop(key, None)

    async def incr(self, key: str, amount: int = 1, ttl: Optional[float] = None) -> int:
        current = await self.get(key)
        try:
            val = int(current) if current is not None else 0
        except (TypeError, ValueError):
            val = 0
        val += amount
        await self.set(key, val, ttl=ttl)
        return val

    async def expire(self, key: str, ttl: float) -> bool:
        async with self._lock:
            item = self._data.get(key)
            if not item:
                return False
            value, _ = item
            self._data[key] = (value, time.monotonic() + float(ttl))
            return True

    async def close(self) -> None:
        async with self._lock:
            self._data.clear()


class RedisCache(AbstractAsyncCache):
    def __init__(self, client: Any) -> None:
        self._client = client

    async def get(self, key: str) -> Optional[Any]:
        return await self._client.get(key)

    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        if ttl is not None:
            await self._client.set(key, value, ex=float(ttl))
        else:
            await self._client.set(key, value)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def incr(self, key: str, amount: int = 1, ttl: Optional[float] = None) -> int:
        new_val = int(await self._client.incrby(key, amount))
        if ttl is not None:
            await self._client.expire(key, float(ttl))
        return new_val

    async def expire(self, key: str, ttl: float) -> bool:
        return bool(await self._client.expire(key, float(ttl)))

    async def close(self) -> None:
        close = getattr(self._client, "close", None)
        if callable(close):
            res = close()
            if hasattr(res, "__await__"):
                await res


async def create_redis_cache(url: str, **kwargs: Any) -> RedisCache:
    try:
        import redis.asyncio as redis_async  # type: ignore

        client = redis_async.Redis.from_url(url, **kwargs)
        return RedisCache(client)
    except Exception:
        pass
    try:
        import aioredis  # type: ignore

        client = await aioredis.from_url(url, **kwargs)
        return RedisCache(client)
    except Exception as exc:
        raise ImportError(
            "No async Redis client available. Install `redis` (>=4) or `aioredis`."
        ) from exc


def create_memory_cache(default_ttl: Optional[float] = None) -> MemoryCache:
    return MemoryCache(default_ttl=default_ttl)


__all__ = [
    "MemoryCache",
    "RedisCache",
    "create_memory_cache",
    "create_redis_cache",
]

