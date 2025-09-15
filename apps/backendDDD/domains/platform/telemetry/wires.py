from __future__ import annotations

from dataclasses import dataclass

import redis.asyncio as redis  # type: ignore

from apps.backendDDD.domains.platform.telemetry.adapters.rum_repository import (
    RumRedisRepository,
)
from apps.backendDDD.domains.platform.telemetry.application.rum_service import (
    RumMetricsService,
)
from apps.backendDDD.packages.core.config import Settings, load_settings


@dataclass
class TelemetryContainer:
    settings: Settings
    rum_service: RumMetricsService


def build_container(settings: Settings | None = None) -> TelemetryContainer:
    s = settings or load_settings()
    client = redis.from_url(str(s.redis_url), decode_responses=True)
    rum_repo = RumRedisRepository(client)
    rum_service = RumMetricsService(rum_repo)
    return TelemetryContainer(settings=s, rum_service=rum_service)


__all__ = ["TelemetryContainer", "build_container"]
