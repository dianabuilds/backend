from __future__ import annotations

from app.domains.navigation.application.ports.cache_port import IKeyValueCache
from app.providers.cache import cache as core_cache


class CoreCacheAdapter(IKeyValueCache):
    async def get(self, key: str) -> str | None:
        return await core_cache.get(key)

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        await core_cache.set(key, value, ttl)

    async def delete(self, *keys: str) -> None:
        await core_cache.delete(*keys)

    async def scan(self, pattern: str) -> list[str]:
        return await core_cache.scan(pattern)
