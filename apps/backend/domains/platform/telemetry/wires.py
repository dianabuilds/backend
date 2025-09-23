from __future__ import annotations

import socket
from dataclasses import dataclass
from urllib.parse import urlparse

import redis.asyncio as redis  # type: ignore

from domains.platform.telemetry.adapters.rum_memory import RumMemoryRepository
from domains.platform.telemetry.adapters.rum_repository import RumRedisRepository
from domains.platform.telemetry.application.rum_service import (
    RumMetricsService,
)
from packages.core.config import Settings, load_settings


@dataclass
class TelemetryContainer:
    settings: Settings
    rum_service: RumMetricsService


def _redis_reachable(url: str) -> bool:
    try:
        u = urlparse(url)
        host = u.hostname or "localhost"
        port = u.port or 6379
        with socket.create_connection((host, port), timeout=0.25):
            return True
    except Exception:
        return False


def build_container(settings: Settings | None = None) -> TelemetryContainer:
    s = settings or load_settings()
    repo = None
    try:
        if _redis_reachable(str(s.redis_url)):
            client = redis.from_url(str(s.redis_url), decode_responses=True)
            repo = RumRedisRepository(client)
    except Exception:
        repo = None
    if repo is None:
        # Fallback to in-memory RUM store in dev/test for visibility
        try:
            from packages.core.config import load_settings as _ls

            if _ls().env != "prod":
                repo = RumMemoryRepository(maxlen=1000)
        except Exception:
            pass
    rum_service = RumMetricsService(repo)
    return TelemetryContainer(settings=s, rum_service=rum_service)


__all__ = ["TelemetryContainer", "build_container"]
