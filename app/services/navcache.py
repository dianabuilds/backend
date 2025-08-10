from __future__ import annotations

import json
from typing import Optional, Dict
from uuid import UUID

from app.core.config import settings
from app.services.cache import Cache, cache
from app.core.log_events import cache_hit, cache_miss, cache_invalidate


class NavCache:
    """Unified cache facade for navigation, modes and compass results."""

    def __init__(self, backend: Cache = cache) -> None:
        self._cache = backend

    # Navigation -----------------------------------------------------
    def _nav_key(self, user_id: str, node_slug: str, mode: str | None) -> str:
        m = mode or "auto"
        return f"nav:{user_id}:{node_slug}:{m}"

    def _mode_key(self, user_id: str, node_slug: str) -> str:
        return f"navm:{user_id}:{node_slug}"

    def _compass_key(self, user_id: str, params_hash: str) -> str:
        return f"comp:{user_id}:{params_hash}"

    async def get_navigation(
        self, user_id: UUID | str, node_slug: str, mode: str | None
    ) -> Optional[Dict]:
        uid = str(user_id)
        key = self._nav_key(uid, node_slug, mode)
        data = await self._cache.get(key)
        if data:
            cache_hit("nav", key, user=uid)
            return json.loads(data)
        cache_miss("nav", key, user=uid)
        return None

    async def set_navigation(
        self,
        user_id: UUID | str,
        node_slug: str,
        mode: str | None,
        payload: Dict,
        ttl_sec: int | None = None,
    ) -> None:
        uid = str(user_id)
        key = self._nav_key(uid, node_slug, mode)
        ttl = ttl_sec or settings.cache.nav_cache_ttl
        await self._cache.set(key, json.dumps(payload), ttl=ttl)

    async def invalidate_navigation_by_node(self, node_slug: str) -> None:
        pattern = f"nav:*:{node_slug}:*"
        keys = await self._cache.scan(pattern)
        if keys:
            await self._cache.delete(*keys)
            cache_invalidate("nav", reason="by_node", key=node_slug)
        # also invalidate modes for this node
        pattern = f"navm:*:{node_slug}"
        keys = await self._cache.scan(pattern)
        if keys:
            await self._cache.delete(*keys)
            cache_invalidate("navm", reason="by_node", key=node_slug)

    async def invalidate_navigation_by_user(self, user_id: UUID | str) -> None:
        uid = str(user_id)
        pattern_nav = f"nav:{uid}:*"
        pattern_mode = f"navm:{uid}:*"
        keys = await self._cache.scan(pattern_nav)
        keys += await self._cache.scan(pattern_mode)
        if keys:
            await self._cache.delete(*keys)
            cache_invalidate("nav", reason="by_user", key=uid)

    async def invalidate_navigation_all(self) -> None:
        patterns = ["nav:*", "navm:*"]
        keys: list[str] = []
        for p in patterns:
            keys += await self._cache.scan(p)
        if keys:
            await self._cache.delete(*keys)
            cache_invalidate("nav", reason="all")

    # Modes ---------------------------------------------------------
    async def get_modes(
        self, user_id: UUID | str, node_slug: str
    ) -> Optional[Dict]:
        uid = str(user_id)
        key = self._mode_key(uid, node_slug)
        data = await self._cache.get(key)
        if data:
            cache_hit("navm", key, user=uid)
            return json.loads(data)
        cache_miss("navm", key, user=uid)
        return None

    async def set_modes(
        self,
        user_id: UUID | str,
        node_slug: str,
        payload: Dict,
        ttl_sec: int | None = None,
    ) -> None:
        uid = str(user_id)
        key = self._mode_key(uid, node_slug)
        ttl = ttl_sec or settings.cache.nav_cache_ttl
        await self._cache.set(key, json.dumps(payload), ttl=ttl)

    async def invalidate_modes_by_node(self, node_slug: str) -> None:
        pattern = f"navm:*:{node_slug}"
        keys = await self._cache.scan(pattern)
        if keys:
            await self._cache.delete(*keys)
            cache_invalidate("navm", reason="by_node", key=node_slug)

    # Compass -------------------------------------------------------
    async def get_compass(
        self, user_id: UUID | str, params_hash: str
    ) -> Optional[Dict]:
        uid = str(user_id)
        key = self._compass_key(uid, params_hash)
        data = await self._cache.get(key)
        if data:
            cache_hit("comp", key, user=uid)
            return json.loads(data)
        cache_miss("comp", key, user=uid)
        return None

    async def set_compass(
        self,
        user_id: UUID | str,
        params_hash: str,
        payload: Dict,
        ttl_sec: int | None = None,
    ) -> None:
        uid = str(user_id)
        key = self._compass_key(uid, params_hash)
        ttl = ttl_sec or settings.cache.compass_cache_ttl
        await self._cache.set(key, json.dumps(payload), ttl=ttl)

    async def invalidate_compass_by_user(self, user_id: UUID | str) -> None:
        uid = str(user_id)
        pattern = f"comp:{uid}:*"
        keys = await self._cache.scan(pattern)
        if keys:
            await self._cache.delete(*keys)
            cache_invalidate("comp", reason="by_user", key=uid)

    async def invalidate_compass_all(self) -> None:
        pattern = "comp:*"
        keys = await self._cache.scan(pattern)
        if keys:
            await self._cache.delete(*keys)
            cache_invalidate("comp", reason="all")


navcache = NavCache()
