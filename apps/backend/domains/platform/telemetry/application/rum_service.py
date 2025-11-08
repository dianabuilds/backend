from __future__ import annotations

import asyncio
import logging
from statistics import mean
from typing import Any

from pydantic import BaseModel, ValidationError

try:  # optional dependency
    from redis.exceptions import RedisError  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - optional
    RedisError = Exception  # type: ignore[misc, assignment]


try:  # optional dependency
    from sqlalchemy.exc import SQLAlchemyError
except ImportError:  # pragma: no cover - optional
    SQLAlchemyError = Exception  # type: ignore[misc, assignment]


from domains.platform.telemetry.ports.rum_port import IRumRepository

log = logging.getLogger(__name__)

_STORAGE_ERRORS = (
    RedisError,
    SQLAlchemyError,
    RuntimeError,
    ValueError,
    TimeoutError,
    asyncio.TimeoutError,
    asyncio.CancelledError,
    ConnectionError,
)


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
            log.debug("RUM repository not configured; dropping event payload")
            return
        try:
            event = RUMEvent.model_validate(payload)
        except ValidationError as exc:
            log.warning("Invalid RUM event payload %s: %s", payload, exc.errors())
            return
        try:
            await self._repo.add(event.model_dump())
        except _STORAGE_ERRORS as exc:  # pragma: no cover - backend failure
            log.exception(
                "Failed to store RUM event %s at %s: %s",
                event.event,
                event.url,
                exc,
            )

    async def list_events(
        self,
        *,
        event: str | None = None,
        url: str | None = None,
        offset: int = 0,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        if self._repo is None:
            return []

        fetch_limit = 1000 if (event or url) else offset + limit
        items = await self._repo.list(fetch_limit)

        if event:
            ev_lower = event.lower()
        if url:
            url_lower = url.lower()

        filtered: list[dict[str, Any]] = []
        for it in items:
            ev = str(it.get("event", "") or "").lower()
            if event and ev_lower not in ev:
                continue
            page_url = str(it.get("url", "") or "").lower()
            if url and url_lower not in page_url:
                continue
            filtered.append(it)

        return filtered[offset : offset + limit]

    async def summary(self, window: int) -> dict[str, Any]:
        items = await self.list_events(limit=window)
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
                if isinstance(d, dict) and isinstance(d.get("dur_ms"), (int, float)):
                    login_durations.append(float(d["dur_ms"]))
            elif ev == "navigation":
                d = it.get("data", {})
                if isinstance(d, dict):
                    if isinstance(d.get("ttfb"), (int, float)):
                        nav_ttfb.append(float(d["ttfb"]))
                    if isinstance(d.get("domContentLoaded"), (int, float)):
                        nav_dcl.append(float(d["domContentLoaded"]))
                    if isinstance(d.get("loadEvent"), (int, float)):
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


__all__ = ["RumMetricsService", "RUMEvent"]
