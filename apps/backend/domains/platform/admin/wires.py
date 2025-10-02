from __future__ import annotations

from dataclasses import dataclass

from packages.core.config import Settings

from .adapters.database import DatabaseProbe
from .adapters.metrics import MetricsProbe
from .adapters.redis import RedisProbe
from .service import AdminService


@dataclass
class AdminContainer:
    service: AdminService


def build_container(settings: Settings) -> AdminContainer:
    db_probe = DatabaseProbe(database_url=str(settings.database_url))
    redis_probe = RedisProbe(redis_url=str(settings.redis_url) if settings.redis_url else None)
    metrics_probe = MetricsProbe()
    service = AdminService(
        settings=settings,
        database_probe=db_probe,
        redis_probe=redis_probe,
        metrics_probe=metrics_probe,
    )
    return AdminContainer(service=service)


__all__ = ["AdminContainer", "build_container"]
