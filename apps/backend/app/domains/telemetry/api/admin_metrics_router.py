from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.core.metrics import metrics_storage
from app.core.transition_metrics import transition_stats
from app.domains.telemetry.application.event_metrics_facade import event_metrics
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(
    prefix="/admin/metrics",
    tags=["admin"],
    dependencies=[Depends(require_admin_role)],
    responses=ADMIN_AUTH_RESPONSES,
)


class MetricsSummary(BaseModel):
    count: int
    error_count: int
    rps: float
    error_rate: float
    p95_latency: float
    p99_latency: float
    count_429: int


class ReliabilityMetrics(BaseModel):
    rps: float
    p95: float
    count_4xx: int
    count_5xx: int
    no_route_percent: float
    fallback_percent: float


_RANGE_MAP = {"1h": 3600, "24h": 24 * 3600}


def _parse_range(range_str: str) -> int:
    return _RANGE_MAP.get(range_str, 3600)


@router.get("/summary", response_model=MetricsSummary)
async def metrics_summary(
    range: Annotated[str, Query()] = "1h",
    profile_id: Annotated[str | None, Query()] = None,
) -> MetricsSummary:  # noqa: A002
    seconds = _parse_range(range)
    summary = metrics_storage.summary(seconds, profile_id)
    return MetricsSummary(**summary)


@router.get("/timeseries")
async def metrics_timeseries(
    range: Annotated[str, Query()] = "1h",  # noqa: A002
    step: Annotated[int, Query(ge=10, le=600)] = 60,
    profile_id: Annotated[str | None, Query()] = None,
):
    """
    Таймсерии: counts per status class (2xx/4xx/5xx) и p95 latency по бакетам.
    """
    seconds = _parse_range(range)
    # нормализуем шаг к 60 либо 300 сек, чтобы не плодить бакеты
    if step < 60:
        step = 60
    elif step > 300:
        step = 300
    data = metrics_storage.timeseries(seconds, step, profile_id)
    return data


@router.get("/reliability", response_model=ReliabilityMetrics)
async def metrics_reliability(
    profile_id: Annotated[str | None, Query()] = None,
) -> ReliabilityMetrics:
    seconds = 3600
    data = metrics_storage.reliability(seconds, profile_id)
    total = data["total"]
    p95 = data["p95"]
    count_4xx = data["count_4xx"]
    count_5xx = data["count_5xx"]
    rps = total / seconds if seconds else 0.0

    stats = transition_stats()
    if profile_id:
        ws_stats = stats.get(profile_id, {})
        no_route_percent = ws_stats.get("no_route_percent", 0.0)
        fallback_percent = ws_stats.get("fallback_used_percent", 0.0)
    else:
        if stats:
            no_route_percent = sum(s.get("no_route_percent", 0.0) for s in stats.values()) / len(
                stats
            )
            fallback_percent = sum(
                s.get("fallback_used_percent", 0.0) for s in stats.values()
            ) / len(stats)
        else:
            no_route_percent = 0.0
            fallback_percent = 0.0
    return ReliabilityMetrics(
        rps=rps,
        p95=p95,
        count_4xx=count_4xx,
        count_5xx=count_5xx,
        no_route_percent=no_route_percent,
        fallback_percent=fallback_percent,
    )


@router.get("/endpoints/top")
async def metrics_top_endpoints(
    range: Annotated[str, Query()] = "1h",  # noqa: A002
    by: Annotated[str, Query(pattern="^(p95|error_rate|rps)$")] = "p95",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    profile_id: Annotated[str | None, Query()] = None,
):
    """
    Топ маршрутов по p95 | error_rate | rps.
    """
    seconds = _parse_range(range)
    data = metrics_storage.top_endpoints(seconds, limit, by, profile_id)
    return {"items": data}


@router.get("/errors/recent")
async def metrics_errors_recent(
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    profile_id: Annotated[str | None, Query()] = None,
):
    """
    Последние ошибки (4xx/5xx).
    """
    return {"items": metrics_storage.recent_errors(limit, profile_id)}


@router.get("/transitions")
async def metrics_transitions():
    return {"stats": transition_stats()}


@router.get("/events")
async def metrics_events():
    return {"counters": event_metrics.snapshot()}
