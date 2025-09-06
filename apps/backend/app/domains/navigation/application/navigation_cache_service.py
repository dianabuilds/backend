from __future__ import annotations

import json
from uuid import UUID

from app.core.cache_keys import cache_key, node_key
from app.core.config import settings
from app.core.log_events import cache_hit, cache_invalidate, cache_miss
from app.domains.navigation.application.ports.cache_port import IKeyValueCache


def _k_nav(user_id: str, slug: str, mode: str, space_id: str | None = None) -> str:
    m = mode or "auto"
    if space_id is not None:
        return cache_key("navigation", space_id, slug, user_id, m)
    return cache_key("navigation", slug, user_id, m)


def _k_navm(user_id: str, slug: str, space_id: str | None = None) -> str:
    if space_id is not None:
        return cache_key("navigation", space_id, slug, "modes", user_id)
    return cache_key("navigation", slug, "modes", user_id)


def _k_comp(user_id: str, phash: str, space_id: str | None = None) -> str:
    if space_id is not None:
        return cache_key("compass", space_id, user_id, phash)
    return cache_key("compass", user_id, phash)


def _idx_node_nav(slug: str, space_id: str | None = None) -> str:
    if space_id is not None:
        return cache_key("node", space_id, slug, "nav")
    return f"{node_key(slug)}:nav"


def _idx_node_navm(slug: str, space_id: str | None = None) -> str:
    if space_id is not None:
        return cache_key("node", space_id, slug, "navm")
    return f"{node_key(slug)}:navm"


def _idx_user_nav(uid: str) -> str:
    return cache_key("user", uid, "nav")


def _idx_user_comp(uid: str) -> str:
    return cache_key("user", uid, "comp")


def _idx_node_comp(slug: str, space_id: str | None = None) -> str:
    if space_id is not None:
        return cache_key("node", space_id, slug, "comp")
    return f"{node_key(slug)}:comp"


class NavigationCacheService:
    """Unified cache facade for navigation, modes and compass results."""

    def __init__(self, cache: IKeyValueCache) -> None:
        self._cache = cache

    # Helpers for JSON-encoded sets of keys (index maintenance)
    async def _get_set(self, key: str) -> set[str]:
        raw = await self._cache.get(key)
        if not raw:
            return set()
        try:
            arr: list[str] = json.loads(raw)
            return {str(x) for x in arr if isinstance(x, str)}
        except Exception:
            return set()

    async def _set_set(self, key: str, s: set[str]) -> None:
        await self._cache.set(key, json.dumps(sorted(list(s))))

    async def _add_to_set(self, key: str, *members: str) -> None:
        cur = await self._get_set(key)
        for m in members:
            cur.add(m)
        await self._set_set(key, cur)

    async def _del_set_key(self, key: str) -> None:
        # just delete the index key
        await self._cache.delete(key)

    # Navigation ---------------------------------------------------------
    async def get_navigation(
        self,
        user_id: UUID | str,
        node_slug: str,
        mode: str | None,
        space_id: UUID | str | None = None,
    ) -> dict | None:
        uid = str(user_id)
        sid = str(space_id) if space_id is not None else None
        key = _k_nav(uid, node_slug, mode or "auto", sid)
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
        payload: dict,
        ttl_sec: int | None = None,
        space_id: UUID | str | None = None,
    ) -> None:
        uid = str(user_id)
        sid = str(space_id) if space_id is not None else None
        key = _k_nav(uid, node_slug, mode or "auto", sid)
        ttl = ttl_sec or settings.cache.nav_cache_ttl
        await self._cache.set(key, json.dumps(payload), ttl)
        await self._add_to_set(_idx_user_nav(uid), key)
        await self._add_to_set(_idx_node_nav(node_slug, sid), key)

    async def invalidate_navigation_by_node(
        self, node_slug: str, space_id: UUID | str | None = None
    ) -> None:
        sid = str(space_id) if space_id is not None else None
        keys = await self._get_set(_idx_node_nav(node_slug, sid))
        count = len(keys)
        if keys:
            await self._cache.delete(*list(keys))
        await self._del_set_key(_idx_node_nav(node_slug, sid))
        keys_modes = await self._get_set(_idx_node_navm(node_slug, sid))
        count += len(keys_modes)
        if keys_modes:
            await self._cache.delete(*list(keys_modes))
        await self._del_set_key(_idx_node_navm(node_slug, sid))
        if count:
            cache_invalidate("nav", reason="by_node", key=node_slug)

    async def invalidate_navigation_by_user(self, user_id: UUID | str) -> None:
        uid = str(user_id)
        idx = _idx_user_nav(uid)
        keys = await self._get_set(idx)
        if keys:
            await self._cache.delete(*list(keys))
        await self._del_set_key(idx)
        if keys:
            cache_invalidate("nav", reason="by_user", key=uid)

    async def invalidate_navigation_all(self) -> None:
        pattern = f"{settings.cache.key_version}:navigation*"
        keys = await self._cache.scan(pattern)
        if keys:
            await self._cache.delete(*keys)
        idx_patterns = [
            f"{settings.cache.key_version}:node:*:nav*",
            f"{settings.cache.key_version}:user:*:nav",
        ]
        for p in idx_patterns:
            idx_keys = await self._cache.scan(p)
            for idx in idx_keys:
                await self._del_set_key(idx)
        if keys:
            cache_invalidate("nav", reason="all")

    # Modes -------------------------------------------------------------
    async def get_modes(
        self, user_id: UUID | str, node_slug: str, space_id: UUID | str | None = None
    ) -> dict | None:
        uid = str(user_id)
        sid = str(space_id) if space_id is not None else None
        key = _k_navm(uid, node_slug, sid)
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
        payload: dict,
        ttl_sec: int | None = None,
        space_id: UUID | str | None = None,
    ) -> None:
        uid = str(user_id)
        sid = str(space_id) if space_id is not None else None
        key = _k_navm(uid, node_slug, sid)
        ttl = ttl_sec or settings.cache.nav_cache_ttl
        await self._cache.set(key, json.dumps(payload), ttl)
        await self._add_to_set(_idx_user_nav(uid), key)
        await self._add_to_set(_idx_node_navm(node_slug, sid), key)

    async def invalidate_modes_by_node(
        self, node_slug: str, space_id: UUID | str | None = None
    ) -> None:
        sid = str(space_id) if space_id is not None else None
        keys = await self._get_set(_idx_node_navm(node_slug, sid))
        if keys:
            await self._cache.delete(*list(keys))
        await self._del_set_key(_idx_node_navm(node_slug, sid))
        if keys:
            cache_invalidate("navm", reason="by_node", key=node_slug)

    # Compass -----------------------------------------------------------
    async def get_compass(
        self,
        user_id: UUID | str,
        params_hash: str,
        space_id: UUID | str | None = None,
    ) -> dict | None:
        uid = str(user_id)
        sid = str(space_id) if space_id is not None else None
        key = _k_comp(uid, params_hash, sid)
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
        payload: dict,
        ttl_sec: int | None = None,
        space_id: UUID | str | None = None,
    ) -> None:
        uid = str(user_id)
        sid = str(space_id) if space_id is not None else None
        key = _k_comp(uid, params_hash, sid)
        ttl = ttl_sec or settings.cache.compass_cache_ttl
        await self._cache.set(key, json.dumps(payload), ttl)
        await self._add_to_set(_idx_user_comp(uid), key)

    async def invalidate_compass_by_user(self, user_id: UUID | str) -> None:
        uid = str(user_id)
        idx = _idx_user_comp(uid)
        keys = await self._get_set(idx)
        if keys:
            await self._cache.delete(*list(keys))
        await self._del_set_key(idx)
        if keys:
            cache_invalidate("comp", reason="by_user", key=uid)

    async def invalidate_compass_by_node(
        self, node_slug: str, space_id: UUID | str | None = None
    ) -> None:
        sid = str(space_id) if space_id is not None else None
        idx = _idx_node_comp(node_slug, sid)
        keys = await self._get_set(idx)
        if keys:
            await self._cache.delete(*list(keys))
        await self._del_set_key(idx)
        if keys:
            cache_invalidate("comp", reason="by_node", key=node_slug)

    async def invalidate_compass_all(self) -> None:
        pattern = f"{settings.cache.key_version}:compass*"
        keys = await self._cache.scan(pattern)
        if keys:
            await self._cache.delete(*keys)
        idx_keys = await self._cache.scan(f"{settings.cache.key_version}:user:*:comp")
        for idx in idx_keys:
            await self._del_set_key(idx)
        if keys:
            cache_invalidate("comp", reason="all")
