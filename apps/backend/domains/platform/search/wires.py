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
from domains.platform.search.adapters.memory_index import InMemoryIndex
from domains.platform.search.adapters.persist_file import (
    FileSearchPersistence,
)
from domains.platform.search.application.service import SearchService
from domains.platform.search.ports import Doc
from packages.core.config import load_settings


@dataclass
class SearchContainer:
    service: SearchService


def build_container() -> SearchContainer:
    backend = InMemoryIndex()
    # Cache: try Redis, fallback to in-memory
    cache = InMemorySearchCache(ttl_seconds=30)
    try:
        s = load_settings()
        if s.redis_url:
            client = redis.from_url(str(s.redis_url), decode_responses=True)
            cache = RedisSearchCache(client, ttl_seconds=30)
    except Exception:
        pass
    # Persistence: file (default path), disabled if cannot init
    persist = None
    try:
        s = load_settings()
        path = getattr(s, "search_persist_path", None)  # optional setting
        if path:
            persist = FileSearchPersistence(str(path))

            # Kick off async warmup to load snapshot into backend without blocking
            async def _warmup() -> None:
                try:
                    docs = await persist.load()  # type: ignore[union-attr]
                    for doc in docs:
                        await backend.upsert(doc)
                except Exception:
                    # Best-effort warmup; ignore failures
                    pass

            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_warmup())
            except RuntimeError:
                # No running loop (e.g., CLI init) — skip warmup
                pass
    except Exception:
        persist = None
    svc = SearchService(index=backend, query=backend, cache=cache, persist=persist)
    return SearchContainer(service=svc)


def register_event_indexers(events: Events, container: SearchContainer) -> None:
    async def _on_profile_updated(_topic: str, payload: dict[str, Any]) -> None:
        pid = str(payload.get("id"))
        title = str(payload.get("username") or payload.get("name") or pid)
        await container.service.upsert(
            Doc(id=f"profile:{pid}", title=title, text=title, tags=("profile",))
        )

    events.on(
        "profile.updated.v1",
        lambda t, p: __import__("asyncio")
        .get_event_loop()
        .create_task(_on_profile_updated(t, p)),
    )


__all__ = ["SearchContainer", "build_container", "register_event_indexers"]
