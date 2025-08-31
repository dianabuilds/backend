from __future__ import annotations

import logging
from collections import deque
from statistics import mean
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import admin_required
from app.domains.users.infrastructure.models.user import User

router = APIRouter(tags=["metrics"])
admin_router = APIRouter(prefix="/admin/telemetry", tags=["admin-telemetry"])

log = logging.getLogger("rum")

# Кольцевой буфер последних событий (в памяти процесса)
_RUM_BUFFER: deque[dict[str, Any]] = deque(maxlen=1000)


def _push_event(payload: dict[str, Any]) -> None:
    try:
        _RUM_BUFFER.append(payload)
    except Exception:
        # не роняем обработчик метрик
        pass


@router.post("/metrics/rum")
async def rum_metrics(request: Request) -> dict[str, Any]:
    """
    Приёмник простых RUM-событий с фронтенда.
    Тело: { event: str, ts: int, url: str, data: any }
    """
    try:
        payload = await request.json()
    except Exception:
        payload = {"parse_error": True}
    # Логируем в общий лог; при необходимости — поменять на запись в БД/метрики
    log.info("RUM %s", payload)
    if isinstance(payload, dict):
        _push_event(payload)
    return {"ok": True}


@admin_router.get("/rum")
async def list_rum_events(
    _admin: Annotated[User, Depends(admin_required)],
    limit: int = Query(200, ge=1, le=1000),
) -> list[dict[str, Any]]:
    """
    Админ: последние RUM-события (по убыванию времени).
    """
    items = list(_RUM_BUFFER)[-limit:]
    items.reverse()
    return items


@admin_router.get("/rum/summary")
async def rum_summary(
    _admin: Annotated[User, Depends(admin_required)],
    window: int = Query(500, ge=1, le=1000),
) -> dict[str, Any]:
    """
    Админ: сводка по последним событиям.
    - counts по event
    - средняя длительность login_attempt.dur_ms
    - навигационные тайминги (средние по окну): ttfb, domContentLoaded, loadEvent
    """
    items = list(_RUM_BUFFER)[-window:]
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
