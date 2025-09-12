from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.domains.telemetry.metrics import metrics_storage
from app.domains.telemetry.transition_metrics import transition_stats
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


@router.get(
    
    "/summary",
    response_model=MetricsSummary,
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "count": 1234,
                        "error_count": 12,
                        "rps": 0.34,
                        "error_rate": 0.0097,
                        "p95_latency": 120.0,
                        "p99_latency": 250.0,
                        "count_429": 3,
                    }
                }
            }
        }
    },
)
async def metrics_summary(
    range: Annotated[str, Query(description="Aggregation window", examples=["1h", "24h"]) ] = "1h",  # noqa: A002
    tenant_id: Annotated[
        str | None,
        Query(description="Filter by tenant", example="ws1"),
    ] = None,
) -> MetricsSummary:  # noqa: A002
    seconds = _parse_range(range)
    summary = metrics_storage.summary(seconds, tenant_id)
    return MetricsSummary(**summary)


@router.get(
    
    "/timeseries",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "step": 60,
                        "from": 1700000000,
                        "to": 1700003600,
                        "series": [
                            {"name": "2xx", "points": [{"ts": 1700000000, "value": 10}]},
                            {"name": "4xx", "points": [{"ts": 1700000000, "value": 1}]},
                            {"name": "5xx", "points": [{"ts": 1700000000, "value": 0}]},
                        ],
                        "p95": [{"ts": 1700000000, "value": 120}],
                    }
                }
            }
        }
    },
)
async def metrics_timeseries(
    range: Annotated[str, Query(description="Aggregation window", examples=["1h", "24h"]) ] = "1h",  # noqa: A002
    step: Annotated[int, Query(ge=10, le=600, description="Bucket size in seconds")] = 60,
    tenant_id: Annotated[str | None, Query(description="Filter by tenant", example="ws1")] = None,
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
    data = metrics_storage.timeseries(seconds, step, tenant_id)
    return data


@router.get(
    
    "/reliability",
    response_model=ReliabilityMetrics,
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "rps": 0.05,
                        "p95": 145.0,
                        "count_4xx": 2,
                        "count_5xx": 1,
                        "no_route_percent": 5.0,
                        "fallback_percent": 1.0,
                    }
                }
            }
        }
    },
)
async def metrics_reliability(
    tenant_id: Annotated[str | None, Query(description="Filter by tenant", example="ws1")] = None,
) -> ReliabilityMetrics:
    seconds = 3600
    data = metrics_storage.reliability(seconds, tenant_id)
    total = data["total"]
    p95 = data["p95"]
    count_4xx = data["count_4xx"]
    count_5xx = data["count_5xx"]
    rps = total / seconds if seconds else 0.0

    stats = transition_stats()
    if tenant_id:
        ws_stats = stats.get(tenant_id, {})
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


@router.get(
    
    "/endpoints/top",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {"route": "/quests/{quest_id}", "p95": 180.0, "error_rate": 0.02, "rps": 0.1, "count": 50}
                        ]
                    }
                }
            }
        }
    },
)
async def metrics_top_endpoints(
    range: Annotated[str, Query(description="Aggregation window", examples=["1h", "24h"]) ] = "1h",  # noqa: A002
    by: Annotated[str, Query(pattern="^(p95|error_rate|rps)$", description="Sort key")] = "p95",
    limit: Annotated[int, Query(ge=1, le=100, description="Max items")] = 20,
    tenant_id: Annotated[str | None, Query(description="Filter by tenant", example="ws1")] = None,
):
    """
    Топ маршрутов по p95 | error_rate | rps.
    """
    seconds = _parse_range(range)
    data = metrics_storage.top_endpoints(seconds, limit, by, tenant_id)
    return {"items": data}


@router.get(
    
    "/errors/recent",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {"ts": 1700000000, "method": "GET", "route": "/x", "status_code": 500, "duration_ms": 120}
                        ]
                    }
                }
            }
        }
    },
)
async def metrics_errors_recent(
    limit: Annotated[int, Query(ge=1, le=500, description="Max items")] = 100,
    tenant_id: Annotated[str | None, Query(description="Filter by tenant", example="ws1")] = None,
):
    """
    Последние ошибки (4xx/5xx).
    """
    return {"items": metrics_storage.recent_errors(limit, tenant_id)}


@router.get("/transitions")
async def metrics_transitions():
    return {"stats": transition_stats()}


@router.get("/events")
async def metrics_events():
    return {"counters": event_metrics.snapshot()}

