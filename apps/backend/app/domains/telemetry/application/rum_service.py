from __future__ import annotations

import logging
from statistics import mean
from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.core.redis_utils import create_async_redis
from app.domains.telemetry.application.ports.rum_port import IRumRepository
from app.domains.telemetry.infrastructure.repositories.rum_repository import (
    RumRedisRepository,
)

log = logging.getLogger(__name__)


class RUMEvent(BaseModel):
    event: str
    ts: int
    url: str
    data: dict[str, Any] | None = None


class RumMetricsService:
    def __init__(self, repo: IRumRepository | None) -> None:
        self._repo = repo

    async def record(self, payload: dict[str, Any]) -> None:
        if self._repo is None:
            return
        try:
            event = RUMEvent.model_validate(payload)
        except ValidationError:
            log.warning("invalid RUM event payload: %s", payload)
            return
        try:
            await self._repo.add(event.model_dump())
        except Exception:  # pragma: no cover - safety
            log.exception("failed to store RUM event")

    async def list_events(self, limit: int) -> list[dict[str, Any]]:
        if self._repo is None:
            return []
        return await self._repo.list(limit)

    async def summary(self, window: int) -> dict[str, Any]:
        items = await self.list_events(window)
        counts: dict[str, int] = {}
        login_durations: list[float] = []
        nav_ttfb: list[float] = []
        nav_dcl: list[float] = []
        nav_load: list[float] = []
        for it in items:
            ev = str(it.get("event", "") or "")
            counts[ev] = counts.get(ev, 0) + 1
            if ev == "login_attempt":
                d = it.get("data", {})
                if isinstance(d, dict) and isinstance(d.get("dur_ms"), int | float):
                    login_durations.append(float(d["dur_ms"]))
            elif ev == "navigation":
                d = it.get("data", {})
                if isinstance(d, dict):
                    if isinstance(d.get("ttfb"), int | float):
                        nav_ttfb.append(float(d["ttfb"]))
                    if isinstance(d.get("domContentLoaded"), int | float):
                        nav_dcl.append(float(d["domContentLoaded"]))
                    if isinstance(d.get("loadEvent"), int | float):
                        nav_load.append(float(d["loadEvent"]))

        def avg(arr: list[float]) -> float | None:
            return round(mean(arr), 2) if arr else None

        return {
            "window": window,
            "counts": counts,
            "login_attempt_avg_ms": avg(login_durations),
            "navigation_avg": {
                "ttfb_ms": avg(nav_ttfb),
                "dom_content_loaded_ms": avg(nav_dcl),
                "load_event_ms": avg(nav_load),
            },
        }


_repo: IRumRepository | None = None
try:
    if settings.redis_url:
        _redis = create_async_redis(settings.redis_url, decode_responses=True)
        _repo = RumRedisRepository(_redis)
except Exception:  # pragma: no cover - safety
    _repo = None

rum_service = RumMetricsService(_repo)

__all__ = ["rum_service", "RumMetricsService"]
