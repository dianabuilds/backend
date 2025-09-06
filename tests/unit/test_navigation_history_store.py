from __future__ import annotations

import asyncio

from app.domains.navigation.infrastructure.history_store import RedisHistoryStore


class DummyCache:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.store.get(key)

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        self.store[key] = value

    async def delete(self, *keys: str) -> None:  # pragma: no cover - unused
        for k in keys:
            self.store.pop(k, None)

    async def scan(self, pattern: str) -> list[str]:  # pragma: no cover - unused
        return []


def test_history_store_roundtrip() -> None:
    cache = DummyCache()
    store = RedisHistoryStore(cache, 3)

    async def scenario() -> None:
        tags, slugs = await store.load("u1")
        assert tags == []
        assert slugs == []
        await store.save("u1", ["t1", "t2"], ["s1"])
        tags, slugs = await store.load("u1")
        assert tags == ["t1", "t2"]
        assert slugs == ["s1"]
        await store.save("u1", ["t1", "t3"], ["s1", "s2", "s3", "s4"])
        tags, slugs = await store.load("u1")
        assert tags == ["t1", "t3"]
        assert slugs == ["s2", "s3", "s4"]

    asyncio.run(scenario())
