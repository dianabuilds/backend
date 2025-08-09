from __future__ import annotations

import fnmatch
import logging
import time
from typing import Any, Dict, List, Optional, Protocol

try:
    import redis.asyncio as redis  # type: ignore
    from redis.exceptions import RedisError
except Exception:  # pragma: no cover - optional dependency
    redis = None
    RedisError = Exception  # type: ignore

from app.core.config import settings

logger = logging.getLogger(__name__)


class Cache(Protocol):
    async def get(self, key: str) -> Optional[str]:
        ...

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        ...

    async def mget(self, keys: List[str]) -> List[Optional[str]]:
        ...

    async def mset(self, mapping: Dict[str, str], ttl: int | None = None) -> None:
        ...

    async def incr(self, key: str, by: int = 1) -> int:
        ...

    async def hincr(self, name: str, field: str, by: int = 1) -> int:
        ...

    async def expire(self, key: str, ttl: int) -> None:
        ...

    async def delete(self, *keys: str) -> None:
        ...

    async def scan(self, pattern: str) -> List[str]:
        ...


class MemoryCache(Cache):
    def __init__(self) -> None:
        self._data: Dict[str, tuple[str, Optional[float]]] = {}
        self._hashes: Dict[str, Dict[str, int]] = {}

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

    async def get(self, key: str) -> Optional[str]:
        if self._expired(key):
            return None
        return self._data[key][0]

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        expires = time.time() + ttl if ttl else None
        self._data[key] = (value, expires)

    async def mget(self, keys: List[str]) -> List[Optional[str]]:
        return [await self.get(k) for k in keys]

    async def mset(self, mapping: Dict[str, str], ttl: int | None = None) -> None:
        for k, v in mapping.items():
            await self.set(k, v, ttl)

    async def incr(self, key: str, by: int = 1) -> int:
        val = int(await self.get(key) or 0) + by
        await self.set(key, str(val))
        return val

    async def hincr(self, name: str, field: str, by: int = 1) -> int:
        h = self._hashes.setdefault(name, {})
        h[field] = h.get(field, 0) + by
        return h[field]

    async def expire(self, key: str, ttl: int) -> None:
        if key in self._data:
            value, _ = self._data[key]
            self._data[key] = (value, time.time() + ttl)

    async def delete(self, *keys: str) -> None:
        for key in keys:
            self._data.pop(key, None)
            self._hashes.pop(key, None)

    async def scan(self, pattern: str) -> List[str]:
        now = time.time()
        keys: List[str] = []
        for key, (_, expires) in list(self._data.items()):
            if expires is not None and expires < now:
                self._data.pop(key, None)
                continue
            if fnmatch.fnmatch(key, pattern):
                keys.append(key)
        return keys


class RedisCache(Cache):
    def __init__(self, url: str) -> None:
        if redis is None:  # pragma: no cover - requires redis
            raise RuntimeError("redis library is not installed")
        self._redis = redis.from_url(url, decode_responses=True)

    async def get(self, key: str) -> Optional[str]:
        return await self._redis.get(key)

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        await self._redis.set(key, value, ex=ttl)

    async def mget(self, keys: List[str]) -> List[Optional[str]]:
        return await self._redis.mget(keys)

    async def mset(self, mapping: Dict[str, str], ttl: int | None = None) -> None:
        if ttl is None:
            await self._redis.mset(mapping)
            return
        async with self._redis.pipeline(transaction=True) as pipe:
            for k, v in mapping.items():
                pipe.set(k, v, ex=ttl)
            await pipe.execute()

    async def incr(self, key: str, by: int = 1) -> int:
        return int(await self._redis.incrby(key, by))

    async def hincr(self, name: str, field: str, by: int = 1) -> int:
        return int(await self._redis.hincrby(name, field, by))

    async def expire(self, key: str, ttl: int) -> None:
        await self._redis.expire(key, ttl)

    async def delete(self, *keys: str) -> None:
        if keys:
            await self._redis.delete(*keys)

    async def scan(self, pattern: str) -> List[str]:
        return [k async for k in self._redis.scan_iter(match=pattern)]


class FallbackCache(Cache):
    def __init__(self, primary: Cache, fallback: Cache) -> None:
        self.primary = primary
        self.fallback = fallback

    async def get(self, key: str) -> Optional[str]:
        try:
            return await self.primary.get(key)
        except Exception as e:  # pragma: no cover - depends on redis
            logger.warning("cache get fallback", exc_info=e)
            return await self.fallback.get(key)

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        try:
            await self.primary.set(key, value, ttl)
        except Exception as e:  # pragma: no cover
            logger.warning("cache set fallback", exc_info=e)
            await self.fallback.set(key, value, ttl)

    async def mget(self, keys: List[str]) -> List[Optional[str]]:
        try:
            return await self.primary.mget(keys)
        except Exception as e:  # pragma: no cover
            logger.warning("cache mget fallback", exc_info=e)
            return await self.fallback.mget(keys)

    async def mset(self, mapping: Dict[str, str], ttl: int | None = None) -> None:
        try:
            await self.primary.mset(mapping, ttl)
        except Exception as e:  # pragma: no cover
            logger.warning("cache mset fallback", exc_info=e)
            await self.fallback.mset(mapping, ttl)

    async def incr(self, key: str, by: int = 1) -> int:
        try:
            return await self.primary.incr(key, by)
        except Exception as e:  # pragma: no cover
            logger.warning("cache incr fallback", exc_info=e)
            return await self.fallback.incr(key, by)

    async def hincr(self, name: str, field: str, by: int = 1) -> int:
        try:
            return await self.primary.hincr(name, field, by)
        except Exception as e:  # pragma: no cover
            logger.warning("cache hincr fallback", exc_info=e)
            return await self.fallback.hincr(name, field, by)

    async def expire(self, key: str, ttl: int) -> None:
        try:
            await self.primary.expire(key, ttl)
        except Exception as e:  # pragma: no cover
            logger.warning("cache expire fallback", exc_info=e)
            await self.fallback.expire(key, ttl)

    async def delete(self, *keys: str) -> None:
        try:
            await self.primary.delete(*keys)
        except Exception as e:  # pragma: no cover
            logger.warning("cache delete fallback", exc_info=e)
            await self.fallback.delete(*keys)

    async def scan(self, pattern: str) -> List[str]:
        try:
            return await self.primary.scan(pattern)
        except Exception as e:  # pragma: no cover
            logger.warning("cache scan fallback", exc_info=e)
            return await self.fallback.scan(pattern)


def _create_cache() -> Cache:
    if settings.redis_url and redis is not None:
        try:
            return FallbackCache(RedisCache(settings.redis_url), MemoryCache())
        except Exception as e:  # pragma: no cover - fallback on init failure
            logger.warning("Failed to init Redis cache, using memory", exc_info=e)
            return MemoryCache()
    return MemoryCache()


cache: Cache = _create_cache()
