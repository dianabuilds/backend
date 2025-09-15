from __future__ import annotations

from dataclasses import dataclass

import redis.asyncio as redis  # type: ignore

from apps.backendDDD.domains.platform.users.adapters.repos_cached import CachedUsersRepo
from apps.backendDDD.domains.platform.users.adapters.repos_sql import SQLUsersRepo
from apps.backendDDD.domains.platform.users.application.service import UsersService
from apps.backendDDD.packages.core.config import Settings, load_settings, to_async_dsn


@dataclass
class UsersContainer:
    settings: Settings
    repo: SQLUsersRepo
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
    svc = UsersService(repo)
    return UsersContainer(settings=s, repo=repo, service=svc)


__all__ = ["UsersContainer", "build_container"]
