from __future__ import annotations

from typing import List, Optional

from app.core.cache import cache as core_cache
from app.domains.navigation.application.ports.cache_port import IKeyValueCache


class CoreCacheAdapter(IKeyValueCache):
    async def get(self, key: str) -> Optional[str]:
        return await core_cache.get(key)

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        await core_cache.set(key, value, ttl)

    async def delete(self, *keys: str) -> None:
        await core_cache.delete(*keys)

    async def scan(self, pattern: str) -> List[str]:
        return await core_cache.scan(pattern)
