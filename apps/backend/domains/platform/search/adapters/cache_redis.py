from __future__ import annotations

import json
import logging
from json import JSONDecodeError

import redis.asyncio as redis  # type: ignore
from redis.exceptions import RedisError  # type: ignore[import]

from domains.platform.search.ports import Hit, SearchCache

logger = logging.getLogger(__name__)


class RedisSearchCache(SearchCache):
    def __init__(self, client: redis.Redis, ttl_seconds: int = 30) -> None:
        self._r = client
        self._ttl = ttl_seconds
        self._ver_key = "search:ver"

    async def _get_ver(self) -> int:
        try:
            value = await self._r.get(self._ver_key)
        except RedisError as exc:
            logger.warning("Failed to read search cache version: %s", exc)
            return 0
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            logger.debug("Invalid search cache version value %r; resetting to 0", value)
            return 0

    async def get(self, key: str) -> list[Hit] | None:
        try:
            raw = await self._r.get(key)
        except RedisError as exc:
            logger.warning("Failed to read search cache entry for %s: %s", key, exc)
            return None
        if not raw:
            return None
        try:
            arr = json.loads(raw)
        except (JSONDecodeError, TypeError) as exc:
            logger.debug("Corrupted search cache payload for %s: %s", key, exc)
            return None
        hits: list[Hit] = []
        for item in arr:
            try:
                hits.append(
                    Hit(
                        id=str(item["id"]),
                        score=float(item["score"]),
                        title=str(item["title"]),
                        tags=tuple(item.get("tags") or ()),
                    )
                )
            except (KeyError, TypeError, ValueError) as exc:
                logger.debug("Skipping invalid search cache hit for %s: %s", key, exc)
        return hits or None

    async def set(self, key: str, hits: list[Hit]) -> None:
        arr = [
            {"id": h.id, "score": h.score, "title": h.title, "tags": list(h.tags)}
            for h in hits
        ]
        try:
            await self._r.set(key, json.dumps(arr), ex=self._ttl)
        except (TypeError, ValueError) as exc:
            logger.warning(
                "Failed to serialize search cache entry for %s: %s", key, exc
            )
        except RedisError as exc:
            logger.warning("Failed to write search cache entry for %s: %s", key, exc)

    async def bump_version(self) -> None:
        try:
            await self._r.incr(self._ver_key)
        except RedisError as exc:
            logger.warning("Failed to increment search cache version: %s", exc)
            try:
                await self._r.set(self._ver_key, 1)
            except RedisError as reset_exc:
                logger.error("Failed to reset search cache version: %s", reset_exc)

    async def versioned_key(self, raw_key: str) -> str:
        v = await self._get_ver()
        return f"search:cache:v{v}:{raw_key}"


__all__ = ["RedisSearchCache"]
