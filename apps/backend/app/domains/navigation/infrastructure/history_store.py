from __future__ import annotations

import json
from collections.abc import Sequence

from app.domains.navigation.application.ports.cache_port import IKeyValueCache
from app.domains.navigation.application.ports.history_port import IUserHistoryStore


class RedisHistoryStore(IUserHistoryStore):
    def __init__(self, cache: IKeyValueCache, max_size: int) -> None:
        self._cache = cache
        self._max = max_size

    def _tag_key(self, user_id: str) -> str:
        return f"nav:history:tags:{user_id}"

    def _slug_key(self, user_id: str) -> str:
        return f"nav:history:slugs:{user_id}"

    async def load(self, user_id: str) -> tuple[list[str], list[str]]:
        tags_raw = await self._cache.get(self._tag_key(user_id)) or "[]"
        slugs_raw = await self._cache.get(self._slug_key(user_id)) or "[]"
        tags = list(json.loads(tags_raw))[-self._max :]
        slugs = list(json.loads(slugs_raw))[-self._max :]
        return tags, slugs

    async def save(self, user_id: str, tags: Sequence[str], slugs: Sequence[str]) -> None:
        tags_list = list(tags)[-self._max :]
        slugs_list = list(slugs)[-self._max :]
        await self._cache.set(self._tag_key(user_id), json.dumps(tags_list))
        await self._cache.set(self._slug_key(user_id), json.dumps(slugs_list))
