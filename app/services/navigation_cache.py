from __future__ import annotations

import json
from typing import Any, Dict, Optional

from app.core.config import settings
from app.services.cache import Cache, cache


class NavigationCache:
    """Simple cache for navigation transitions."""

    def __init__(self, backend: Cache = cache) -> None:
        self.ttl = int(settings.navigation_ttl_hours * 3600)
        self._cache = backend

    def _key(self, user_id: str | None, node_id: str) -> str:
        uid = user_id or "anon"
        return f"navigation:{uid}:{node_id}"

    async def get(self, user_id: str | None, node_id: str) -> Optional[Dict[str, Any]]:
        key = self._key(user_id, node_id)
        data = await self._cache.get(key)
        if data is None:
            return None
        return json.loads(data)

    async def set(self, user_id: str | None, node_id: str, data: Dict[str, Any]) -> None:
        key = self._key(user_id, node_id)
        await self._cache.set(key, json.dumps(data), ttl=self.ttl)

    async def invalidate(self, user_id: str | None, node_id: str) -> None:
        key = self._key(user_id, node_id)
        await self._cache.delete(key)

    async def invalidate_all_for_node(self, node_id: str) -> None:
        pattern = f"navigation:*:{node_id}"
        keys = await self._cache.scan(pattern)
        if keys:
            await self._cache.delete(*keys)


navigation_cache = NavigationCache()
