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
async def test_cache_hit_miss_without_account_scope() -> None:
    cache = DummyCache()
    svc = NavigationCacheService(cache)
    user = uuid.uuid4()
    slug = "node"
    account_a = uuid.uuid4()
    account_b = uuid.uuid4()
    payload = {"t": []}

    await svc.set_navigation(user, slug, "auto", payload, account_id=account_a)

    for _ in range(20):
        assert await svc.get_navigation(user, slug, "auto", account_id=account_a) == payload

    # account_id is ignored and should return cached payload
    assert await svc.get_navigation(user, slug, "auto", account_id=account_b) == payload


@pytest.mark.asyncio
async def test_invalidate_by_node() -> None:
    cache = DummyCache()
    svc = NavigationCacheService(cache)
    user = uuid.uuid4()
    slug = "node"
    account_a = uuid.uuid4()
    payload = {"t": []}

    await svc.set_navigation(user, slug, "auto", payload, account_id=account_a)

    await svc.invalidate_navigation_by_node(account_id=account_a, node_slug=slug)

    assert await svc.get_navigation(user, slug, "auto", account_id=account_a) is None
