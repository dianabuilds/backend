from __future__ import annotations

import json
from typing import Dict, Optional
from uuid import UUID

from app.core.config import settings
from app.core.log_events import cache_hit, cache_miss, cache_invalidate
from app.services.cache_backends import redis_cache, MemoryCache


# key helpers -------------------------------------------------------------

def k_nav(user_id: str, slug: str, mode: str, v: str | None = None) -> str:
    version = v or settings.cache.key_version
    m = mode or "auto"
    return f"{version}:nav:{user_id}:{slug}:{m}"


def k_navm(user_id: str, slug: str, v: str | None = None) -> str:
    version = v or settings.cache.key_version
    return f"{version}:navm:{user_id}:{slug}"


def k_comp(user_id: str, phash: str, v: str | None = None) -> str:
    version = v or settings.cache.key_version
    return f"{version}:comp:{user_id}:{phash}"


def idx_node_nav(slug: str, v: str | None = None) -> str:
    version = v or settings.cache.key_version
    return f"{version}:idx:node->nav:{slug}"


def idx_node_navm(slug: str, v: str | None = None) -> str:
    version = v or settings.cache.key_version
    return f"{version}:idx:node->navm:{slug}"


def idx_user_nav(uid: str, v: str | None = None) -> str:
    version = v or settings.cache.key_version
    return f"{version}:idx:user->nav:{uid}"


def idx_user_comp(uid: str, v: str | None = None) -> str:
    version = v or settings.cache.key_version
    return f"{version}:idx:user->comp:{uid}"


def idx_node_comp(slug: str, v: str | None = None) -> str:
    version = v or settings.cache.key_version
    return f"{version}:idx:node->comp:{slug}"


class NavCache:
    """Unified cache facade for navigation, modes and compass results."""

    def __init__(self, backend=redis_cache) -> None:
        self._cache = backend

    # Navigation ---------------------------------------------------------
    async def get_navigation(
        self, user_id: UUID | str, node_slug: str, mode: str | None
    ) -> Optional[Dict]:
        uid = str(user_id)
        key = k_nav(uid, node_slug, mode or "auto")
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
        key = k_nav(uid, node_slug, mode or "auto")
        ttl = ttl_sec or settings.cache.nav_cache_ttl
        await self._cache.setex(key, ttl, json.dumps(payload))
        await self._cache.sadd(idx_user_nav(uid), key)
        await self._cache.sadd(idx_node_nav(node_slug), key)

    async def invalidate_navigation_by_node(self, node_slug: str) -> None:
        keys = await self._cache.smembers(idx_node_nav(node_slug))
        count = len(keys)
        await self._cache.delete_many(keys)
        await self._cache.delete_key(idx_node_nav(node_slug))
        keys_modes = await self._cache.smembers(idx_node_navm(node_slug))
        count += len(keys_modes)
        await self._cache.delete_many(keys_modes)
        await self._cache.delete_key(idx_node_navm(node_slug))
        if count:
            cache_invalidate("nav", reason="by_node", key=node_slug)

    async def invalidate_navigation_by_user(self, user_id: UUID | str) -> None:
        uid = str(user_id)
        idx = idx_user_nav(uid)
        keys = await self._cache.smembers(idx)
        await self._cache.delete_many(keys)
        await self._cache.delete_key(idx)
        if keys:
            cache_invalidate("nav", reason="by_user", key=uid)

    async def invalidate_navigation_all(self) -> None:
        pattern = f"{settings.cache.key_version}:nav*"
        keys = await self._cache.scan(pattern)
        await self._cache.delete_many(keys)
        if keys:
            cache_invalidate("nav", reason="all")

    # Modes -------------------------------------------------------------
    async def get_modes(
        self, user_id: UUID | str, node_slug: str
    ) -> Optional[Dict]:
        uid = str(user_id)
        key = k_navm(uid, node_slug)
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
        key = k_navm(uid, node_slug)
        ttl = ttl_sec or settings.cache.nav_cache_ttl
        await self._cache.setex(key, ttl, json.dumps(payload))
        await self._cache.sadd(idx_user_nav(uid), key)
        await self._cache.sadd(idx_node_navm(node_slug), key)

    async def invalidate_modes_by_node(self, node_slug: str) -> None:
        keys = await self._cache.smembers(idx_node_navm(node_slug))
        await self._cache.delete_many(keys)
        await self._cache.delete_key(idx_node_navm(node_slug))
        if keys:
            cache_invalidate("navm", reason="by_node", key=node_slug)

    # Compass -----------------------------------------------------------
    async def get_compass(
        self, user_id: UUID | str, params_hash: str
    ) -> Optional[Dict]:
        uid = str(user_id)
        key = k_comp(uid, params_hash)
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
        key = k_comp(uid, params_hash)
        ttl = ttl_sec or settings.cache.compass_cache_ttl
        await self._cache.setex(key, ttl, json.dumps(payload))
        await self._cache.sadd(idx_user_comp(uid), key)

    async def invalidate_compass_by_user(self, user_id: UUID | str) -> None:
        uid = str(user_id)
        idx = idx_user_comp(uid)
        keys = await self._cache.smembers(idx)
        await self._cache.delete_many(keys)
        await self._cache.delete_key(idx)
        if keys:
            cache_invalidate("comp", reason="by_user", key=uid)

    async def invalidate_compass_by_node(self, node_slug: str) -> None:
        idx = idx_node_comp(node_slug)
        keys = await self._cache.smembers(idx)
        await self._cache.delete_many(keys)
        await self._cache.delete_key(idx)
        if keys:
            cache_invalidate("comp", reason="by_node", key=node_slug)

    async def invalidate_compass_all(self) -> None:
        pattern = f"{settings.cache.key_version}:comp*"
        keys = await self._cache.scan(pattern)
        await self._cache.delete_many(keys)
        idx_keys = await self._cache.scan(
            f"{settings.cache.key_version}:idx:user->comp:*"
        )
        for idx in idx_keys:
            await self._cache.delete_key(idx)
        if keys:
            cache_invalidate("comp", reason="all")


navcache = NavCache()
