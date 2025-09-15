from __future__ import annotations

from dataclasses import dataclass

import redis.asyncio as redis  # type: ignore

from domains.platform.flags.adapters.store_memory import (
    InMemoryFlagStore,
)
from domains.platform.flags.adapters.store_redis import RedisFlagStore
from domains.platform.flags.application.service import FlagService
from packages.core.config import Settings, load_settings


@dataclass
class FlagsContainer:
    settings: Settings
    store: InMemoryFlagStore | RedisFlagStore
    service: FlagService


def build_container(settings: Settings | None = None) -> FlagsContainer:
    s = settings or load_settings()
    store = InMemoryFlagStore()
    try:
        if s.redis_url:
            client = redis.from_url(str(s.redis_url), decode_responses=True)
            store = RedisFlagStore(client)
    except Exception:
        pass
    svc = FlagService(store=store)
    return FlagsContainer(settings=s, store=store, service=svc)


__all__ = ["FlagsContainer", "build_container"]
