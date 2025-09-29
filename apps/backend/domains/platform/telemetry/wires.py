from __future__ import annotations

import socket
from dataclasses import dataclass
from urllib.parse import urlparse

import redis.asyncio as redis  # type: ignore

from domains.platform.telemetry.adapters.rum_memory import RumMemoryRepository
from domains.platform.telemetry.adapters.rum_repository import RumRedisRepository
from domains.platform.telemetry.adapters.rum_sql import RumSQLRepository
from domains.platform.telemetry.application.rum_service import (
    RumMetricsService,
)
from domains.platform.telemetry.ports.rum_port import IRumRepository
from packages.core.config import Settings, load_settings, to_async_dsn


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


def _database_dsn(settings: Settings) -> str | None:
    raw = getattr(settings, "database_url", None)
    if not raw:
        return None
    try:
        dsn = to_async_dsn(raw)
    except Exception:
        return None
    if isinstance(dsn, str):
        if "?" in dsn:
            return dsn.split("?", 1)[0]
        return dsn
    return None


def build_container(settings: Settings | None = None) -> TelemetryContainer:
    s = settings or load_settings()
    repo: IRumRepository | None = None

    dsn = _database_dsn(s)
    if dsn:
        try:
            repo = RumSQLRepository(dsn)
        except Exception:
            repo = None

    if repo is None:
        try:
            if _redis_reachable(str(s.redis_url)):
                client = redis.from_url(str(s.redis_url), decode_responses=True)
                repo = RumRedisRepository(client)
        except Exception:
            repo = None

    if repo is None and getattr(s, "env", None) != "prod":
        repo = RumMemoryRepository(maxlen=1000)

    rum_service = RumMetricsService(repo)
    return TelemetryContainer(settings=s, rum_service=rum_service)


__all__ = ["TelemetryContainer", "build_container"]
