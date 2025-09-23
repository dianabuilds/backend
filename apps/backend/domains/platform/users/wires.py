from __future__ import annotations

from dataclasses import dataclass

import redis.asyncio as redis  # type: ignore

from domains.platform.users.adapters.repos_cached import CachedUsersRepo
from domains.platform.users.adapters.repos_sql import SQLUsersRepo
from domains.platform.users.application.service import UsersService
from domains.platform.users.ports import UsersRepo
from packages.core.config import Settings, load_settings, to_async_dsn


@dataclass
class UsersContainer:
    settings: Settings
    repo: UsersRepo
    service: UsersService


def build_container(settings: Settings | None = None) -> UsersContainer:
    s = settings or load_settings()
    base = SQLUsersRepo(to_async_dsn(s.database_url))
    repo = base
    try:
        if s.redis_url:
            client = redis.from_url(str(s.redis_url), decode_responses=True)
            repo = CachedUsersRepo(base, client, ttl_seconds=60)
    except Exception:
        repo = base
    svc = UsersService(repo=repo, settings=s)
    return UsersContainer(settings=s, repo=repo, service=svc)


__all__ = ["UsersContainer", "build_container"]
