from __future__ import annotations

import fnmatch
import time
from typing import Any, Iterable

try:  # pragma: no cover - optional dependency
    from redis.asyncio import Redis  # type: ignore
except Exception:  # pragma: no cover - redis not installed
    Redis = None  # type: ignore

from app.core.config import settings


class RedisCache:
    def __init__(self, url: str):
        if Redis is None:
            raise RuntimeError("redis library is not installed")
        self._r = Redis.from_url(url, decode_responses=True)

    async def get(self, key: str) -> str | None:
        return await self._r.get(key)

    async def setex(self, key: str, ttl: int, payload: str) -> None:
        await self._r.setex(key, ttl, payload)

    async def sadd(self, key: str, *members: str) -> int:
        return await self._r.sadd(key, *members)

    async def smembers(self, key: str) -> set[str]:
        return await self._r.smembers(key)

    async def delete_many(self, keys: Iterable[str]) -> None:
        keys = list(keys)
        if not keys:
            return
        pipe = self._r.pipeline(transaction=False)
        for k in keys:
            pipe.unlink(k)
        await pipe.execute()

    async def delete_key(self, key: str) -> None:
        await self._r.unlink(key)

    async def scan(self, pattern: str) -> list[str]:
        return [k async for k in self._r.scan_iter(match=pattern)]

    async def close(self) -> None:
        await self._r.aclose()

    async def ttl(self, key: str) -> int:
        return await self._r.ttl(key)


class MemoryCache:
    def __init__(self) -> None:
        self._data: dict[str, tuple[str, float | None]] = {}
        self._sets: dict[str, set[str]] = {}

    def _expired(self, key: str) -> bool:
        value = self._data.get(key)
        if value is None:
            return True
        _, expires = value
        if expires is None:
            return False
        if expires < time.time():
            self._data.pop(key, None)
            return True
        return False

    async def get(self, key: str) -> str | None:
        if self._expired(key):
            return None
        return self._data[key][0]

    async def setex(self, key: str, ttl: int, payload: str) -> None:
        self._data[key] = (payload, time.time() + ttl if ttl else None)

    async def sadd(self, key: str, *members: str) -> int:
        s = self._sets.setdefault(key, set())
        before = len(s)
        s.update(members)
        return len(s) - before

    async def smembers(self, key: str) -> set[str]:
        return set(self._sets.get(key, set()))

    async def delete_many(self, keys: Iterable[str]) -> None:
        for k in keys:
            self._data.pop(k, None)

    async def delete_key(self, key: str) -> None:
        self._data.pop(key, None)
        self._sets.pop(key, None)

    async def scan(self, pattern: str) -> list[str]:
        keys: list[str] = []
        now = time.time()
        for key, (val, exp) in list(self._data.items()):
            if exp is not None and exp < now:
                self._data.pop(key, None)
                continue
            if fnmatch.fnmatch(key, pattern):
                keys.append(key)
        for key in self._sets.keys():
            if fnmatch.fnmatch(key, pattern):
                keys.append(key)
        return keys

    async def ttl(self, key: str) -> int:
        if self._expired(key):
            return -2
        _, exp = self._data.get(key, (None, None))
        if exp is None:
            return -1
        return int(exp - time.time())


class FallbackCache:
    def __init__(self, primary: RedisCache | None, fallback: MemoryCache):
        self.primary = primary
        self.fallback = fallback

    async def _call(self, method: str, *args, **kwargs):
        if self.primary is not None:
            try:
                func = getattr(self.primary, method)
                return await func(*args, **kwargs)
            except Exception:
                self.primary = None
        func = getattr(self.fallback, method)
        return await func(*args, **kwargs)

    async def get(self, key: str) -> str | None:
        return await self._call("get", key)

    async def setex(self, key: str, ttl: int, payload: str) -> None:
        await self._call("setex", key, ttl, payload)

    async def sadd(self, key: str, *members: str) -> int:
        return await self._call("sadd", key, *members)

    async def smembers(self, key: str) -> set[str]:
        return await self._call("smembers", key)

    async def delete_many(self, keys: Iterable[str]) -> None:
        await self._call("delete_many", keys)

    async def delete_key(self, key: str) -> None:
        await self._call("delete_key", key)

    async def scan(self, pattern: str) -> list[str]:
        return await self._call("scan", pattern)

    async def ttl(self, key: str) -> int:
        return await self._call("ttl", key)


def _create_cache() -> FallbackCache | MemoryCache:
    url = settings.cache.redis_url
    if url:
        try:
            primary = RedisCache(url)
            return FallbackCache(primary, MemoryCache())
        except Exception:
            pass
    return MemoryCache()


redis_cache = _create_cache()
