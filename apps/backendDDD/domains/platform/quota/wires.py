from __future__ import annotations

from dataclasses import dataclass

import redis.asyncio as redis  # type: ignore

from apps.backendDDD.domains.platform.quota.adapters.redis_dao import RedisQuotaDAO
from apps.backendDDD.domains.platform.quota.application.service import QuotaService
from apps.backendDDD.packages.core.config import Settings, load_settings


@dataclass
class QuotaContainer:
    settings: Settings
    service: QuotaService


def build_container(settings: Settings | None = None) -> QuotaContainer:
    s = settings or load_settings()
    client = redis.from_url(str(s.redis_url), decode_responses=True)
    dao = RedisQuotaDAO(client)
    svc = QuotaService(dao)
    return QuotaContainer(settings=s, service=svc)


__all__ = ["QuotaContainer", "build_container"]
