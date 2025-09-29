from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import redis.asyncio as redis  # type: ignore

from domains.platform.events.service import Events
from domains.platform.search.adapters.cache_memory import (
    InMemorySearchCache,
)
from domains.platform.search.adapters.cache_redis import (
    RedisSearchCache,
)
from domains.platform.search.adapters.index_sql import SQLSearchIndex
from domains.platform.search.adapters.memory_index import InMemoryIndex
from domains.platform.search.adapters.persist_file import (
    FileSearchPersistence,
)
from domains.platform.search.application.service import SearchService
from domains.platform.search.ports import Doc, SearchCache
from packages.core.config import Settings, load_settings, to_async_dsn


@dataclass
class SearchContainer:
    service: SearchService


def _database_dsn(settings: Settings) -> str | None:
    raw = getattr(settings, "database_url", None)
    if not raw:
        return None
    try:
        dsn = to_async_dsn(raw)
    except Exception:
        return None
    if isinstance(dsn, str) and "?" in dsn:
        return dsn.split("?", 1)[0]
    return dsn if isinstance(dsn, str) else None


def build_container(settings: Settings | None = None) -> SearchContainer:
    s = settings or load_settings()

    dsn = _database_dsn(s)
    backend: InMemoryIndex | SQLSearchIndex
    if dsn:
        try:
            backend = SQLSearchIndex(dsn)
        except Exception:
            backend = InMemoryIndex()
    else:
        backend = InMemoryIndex()

    cache: SearchCache = InMemorySearchCache(ttl_seconds=30)
    try:
        if s.redis_url:
            client = redis.from_url(str(s.redis_url), decode_responses=True)
            cache = RedisSearchCache(client, ttl_seconds=30)
    except Exception:
        pass

    persist = None
    path = getattr(s, "search_persist_path", None)
    if path:
        persist = FileSearchPersistence(str(path))

        async def _warmup() -> None:
            try:
                docs = await persist.load()  # type: ignore[union-attr]
                for doc in docs:
                    await backend.upsert(doc)
            except Exception:
                pass

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(_warmup())
        else:
            loop.create_task(_warmup())

    svc = SearchService(index=backend, query=backend, cache=cache, persist=persist)
    return SearchContainer(service=svc)


def register_event_indexers(events: Events, container: SearchContainer) -> None:
    async def _on_profile_updated(_topic: str, payload: dict[str, Any]) -> None:
        pid = str(payload.get("id"))
        title = str(payload.get("username") or payload.get("name") or pid)
        await container.service.upsert(
            Doc(id=f"profile:{pid}", title=title, text=title, tags=("profile",))
        )

    def _schedule_profile_update(topic: str, payload: dict[str, Any]) -> None:
        try:
            asyncio.get_running_loop().create_task(_on_profile_updated(topic, payload))
        except RuntimeError:
            asyncio.run(_on_profile_updated(topic, payload))

    events.on("profile.updated.v1", _schedule_profile_update)


__all__ = ["SearchContainer", "build_container", "register_event_indexers"]
