from __future__ import annotations

from dataclasses import dataclass

import redis.asyncio as redis  # type: ignore

from domains.platform.flags.adapters.store_redis import RedisFlagStore
from domains.platform.flags.application.service import FlagService
from packages.core.config import Settings, load_settings


@dataclass
class FlagsContainer:
    settings: Settings
    store: RedisFlagStore
    service: FlagService


def build_container(settings: Settings | None = None) -> FlagsContainer:
    s = settings or load_settings()
    if not s.redis_url:
        raise RuntimeError("redis_url is required for FlagService")
    client = redis.from_url(str(s.redis_url), decode_responses=True)
    store = RedisFlagStore(client)
    svc = FlagService(store=store)
    return FlagsContainer(settings=s, store=store, service=svc)


__all__ = ["FlagsContainer", "build_container"]
