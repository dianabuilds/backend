from __future__ import annotations

import importlib
import sys
import uuid

import pytest

sys.modules.setdefault("app", importlib.import_module("apps.backend.app"))

from app.domains.navigation.application.navigation_cache_service import (  # noqa: E402
    NavigationCacheService,
)
from app.domains.navigation.application.ports.cache_port import IKeyValueCache  # noqa: E402


class DummyCache(IKeyValueCache):
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.store.get(key)

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        self.store[key] = value

    async def delete(self, *keys: str) -> None:
        for k in keys:
            self.store.pop(k, None)

    async def scan(self, pattern: str) -> list[str]:  # pragma: no cover - unused
        return []


@pytest.mark.asyncio
async def test_cache_hit_miss_with_space_id() -> None:
    cache = DummyCache()
    svc = NavigationCacheService(cache)
    user = uuid.uuid4()
    slug = "node"
    space_a = uuid.uuid4()
    space_b = uuid.uuid4()
    payload = {"t": []}

    await svc.set_navigation(user, slug, "auto", payload, space_id=space_a)

    for _ in range(20):
        assert await svc.get_navigation(user, slug, "auto", space_id=space_a) == payload

    assert await svc.get_navigation(user, slug, "auto", space_id=space_b) is None


@pytest.mark.asyncio
async def test_invalidate_by_space() -> None:
    cache = DummyCache()
    svc = NavigationCacheService(cache)
    user = uuid.uuid4()
    slug = "node"
    space_a = uuid.uuid4()
    space_b = uuid.uuid4()
    payload = {"t": []}

    await svc.set_navigation(user, slug, "auto", payload, space_id=space_a)
    await svc.set_navigation(user, slug, "auto", payload, space_id=space_b)

    await svc.invalidate_navigation_by_node(space_a, slug)

    assert await svc.get_navigation(user, slug, "auto", space_id=space_a) is None
    assert await svc.get_navigation(user, slug, "auto", space_id=space_b) == payload
