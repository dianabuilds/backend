from __future__ import annotations

import json

import redis.asyncio as redis  # type: ignore

from domains.platform.search.ports import Hit, SearchCache


class RedisSearchCache(SearchCache):
    def __init__(self, client: redis.Redis, ttl_seconds: int = 30) -> None:
        self._r = client
        self._ttl = ttl_seconds
        self._ver_key = "search:ver"

    async def _get_ver(self) -> int:
        v = await self._r.get(self._ver_key)
        try:
            return int(v or 0)
        except Exception:
            return 0

    async def get(self, key: str) -> list[Hit] | None:
        raw = await self._r.get(key)
        if not raw:
            return None
        try:
            arr = json.loads(raw)
            hits: list[Hit] = []
            for h in arr:
                hits.append(
                    Hit(
                        id=str(h["id"]),
                        score=float(h["score"]),
                        title=str(h["title"]),
                        tags=tuple(h.get("tags") or ()),
                    )
                )
            return hits
        except Exception:
            return None

    async def set(self, key: str, hits: list[Hit]) -> None:
        arr = [{"id": h.id, "score": h.score, "title": h.title, "tags": list(h.tags)} for h in hits]
        await self._r.set(key, json.dumps(arr), ex=self._ttl)

    async def bump_version(self) -> None:
        try:
            await self._r.incr(self._ver_key)
        except Exception:
            await self._r.set(self._ver_key, 1)

    async def versioned_key(self, raw_key: str) -> str:
        v = await self._get_ver()
        return f"search:cache:v{v}:{raw_key}"


__all__ = ["RedisSearchCache"]
