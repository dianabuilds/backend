from __future__ import annotations

import logging
import socket
from dataclasses import dataclass
from urllib.parse import urlparse

try:
    import redis.asyncio as redis  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - optional dependency
    redis = None  # type: ignore[assignment]

try:
    from redis.exceptions import RedisError  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - optional dependency
    RedisError = Exception  # type: ignore[misc, assignment]

from sqlalchemy.exc import SQLAlchemyError

from domains.platform.telemetry.adapters.rum_memory import RumMemoryRepository
from domains.platform.telemetry.adapters.rum_repository import RumRedisRepository
from domains.platform.telemetry.adapters.rum_sql import RumSQLRepository
from domains.platform.telemetry.application.rum_service import (
    RumMetricsService,
)
from domains.platform.telemetry.ports.rum_port import IRumRepository
from packages.core.config import Settings, load_settings, to_async_dsn

logger = logging.getLogger(__name__)


@dataclass
class TelemetryContainer:
    settings: Settings
    rum_service: RumMetricsService
    rum_repository: IRumRepository | None


def _redis_reachable(url: str) -> bool:
    try:
        u = urlparse(url)
        host = u.hostname or "localhost"
        port = u.port or 6379
        with socket.create_connection((host, port), timeout=0.25):
            return True
    except OSError as exc:
        logger.debug("Redis probe to %s failed: %s", url, exc)
        return False


def _database_dsn(settings: Settings) -> str | None:
    raw = getattr(settings, "database_url", None)
    if not raw:
        return None
    try:
        dsn = to_async_dsn(raw)
    except (TypeError, ValueError) as exc:
        logger.warning("Telemetry database DSN is invalid, falling back: %s", exc)
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
        except ImportError as exc:
            logger.warning("Telemetry SQL repository dependency missing: %s", exc)
        except SQLAlchemyError as exc:
            logger.error("Telemetry SQL repository init failed: %s", exc)
        except RuntimeError as exc:
            logger.error("Telemetry SQL repository misconfigured: %s", exc)

    if repo is None:
        if redis is None:
            logger.info("Telemetry Redis backend not installed, skipping")
        else:
            try:
                if _redis_reachable(str(s.redis_url)):
                    client = redis.from_url(str(s.redis_url), decode_responses=True)
                    repo = RumRedisRepository(client)
                else:
                    logger.info("Telemetry Redis backend not reachable, skipping")
            except RedisError as exc:
                logger.error("Telemetry Redis repository init failed: %s", exc)
            except (OSError, ValueError) as exc:
                logger.error("Telemetry Redis repository misconfigured: %s", exc)

    if repo is None and getattr(s, "env", None) != "prod":
        logger.info(
            "Telemetry repository falling back to in-memory store for %s",
            getattr(s, "env", "unknown"),
        )
        repo = RumMemoryRepository(maxlen=1000)

    rum_service = RumMetricsService(repo)
    return TelemetryContainer(settings=s, rum_service=rum_service, rum_repository=repo)


__all__ = ["TelemetryContainer", "build_container"]
