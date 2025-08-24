from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.core.metrics import metrics_storage, transition_stats
from app.domains.telemetry.application.event_metrics_facade import event_metrics
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(
    prefix="/admin/metrics",
    tags=["admin"],
    dependencies=[Depends(require_admin_role())],
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


_RANGE_MAP = {"1h": 3600, "24h": 24 * 3600}


def _parse_range(range_str: str) -> int:
    return _RANGE_MAP.get(range_str, 3600)


@router.get("/summary", response_model=MetricsSummary)
async def metrics_summary(range: str = Query("1h")) -> MetricsSummary:  # noqa: A002
    seconds = _parse_range(range)
    summary = metrics_storage.summary(seconds)
    return MetricsSummary(**summary)


@router.get("/timeseries")
async def metrics_timeseries(
    range: str = Query("1h"),  # noqa: A002
    step: int = Query(60, ge=10, le=600),
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
    data = metrics_storage.timeseries(seconds, step)
    return data


@router.get("/endpoints/top")
async def metrics_top_endpoints(
    range: str = Query("1h"),  # noqa: A002
    by: str = Query("p95", pattern="^(p95|error_rate|rps)$"),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Топ маршрутов по p95 | error_rate | rps.
    """
    seconds = _parse_range(range)
    data = metrics_storage.top_endpoints(seconds, limit, by)
    return {"items": data}


@router.get("/errors/recent")
async def metrics_errors_recent(limit: int = Query(100, ge=1, le=500)):
    """
    Последние ошибки (4xx/5xx).
    """
    return {"items": metrics_storage.recent_errors(limit)}


@router.get("/transitions")
async def metrics_transitions():
    return {"stats": transition_stats()}


@router.get("/events")
async def metrics_events():
    return {"counters": event_metrics.snapshot()}
