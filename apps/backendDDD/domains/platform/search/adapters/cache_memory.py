from __future__ import annotations

import time

from apps.backendDDD.domains.platform.search.ports import Hit, SearchCache


class InMemorySearchCache(SearchCache):
    def __init__(self, ttl_seconds: int = 30) -> None:
        self._ttl = ttl_seconds
        self._ver = 0
        self._data: dict[str, tuple[float, list[Hit]]] = {}

    async def get(self, key: str) -> list[Hit] | None:
        now = time.time()
        item = self._data.get(key)
        if not item:
            return None
        exp, payload = item
        if exp < now:
            self._data.pop(key, None)
            return None
        return payload

    async def set(self, key: str, hits: list[Hit]) -> None:
        self._data[key] = (time.time() + self._ttl, hits)

    async def bump_version(self) -> None:
        self._ver += 1
        # Drop cache wholesale on version bump to keep things simple
        self._data.clear()

    async def versioned_key(self, raw_key: str) -> str:
        return f"v{self._ver}:{raw_key}"


__all__ = ["InMemorySearchCache"]
