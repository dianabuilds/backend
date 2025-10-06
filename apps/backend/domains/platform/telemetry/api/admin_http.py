from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request

from apps.backend import get_container
from domains.platform.iam.security import require_admin
from domains.platform.telemetry.application.event_metrics_service import event_metrics
from domains.platform.telemetry.application.metrics_registry import llm_metrics
from domains.platform.telemetry.application.transition_metrics_service import (
    transition_metrics,
)
from domains.platform.telemetry.application.ux_metrics_service import ux_metrics
from domains.platform.telemetry.application.worker_metrics_service import worker_metrics
from packages.fastapi_rate_limit import optional_rate_limiter

try:
    from prometheus_client import REGISTRY  # type: ignore
except ImportError:  # pragma: no cover
    REGISTRY = None  # type: ignore


def make_router() -> APIRouter:
    router = APIRouter(
        prefix="/v1/admin/telemetry", tags=["admin-telemetry"]
    )  # guarded per-route

    @router.get(
        "/rum",
        dependencies=(optional_rate_limiter(times=60, seconds=60)),
    )
    async def list_rum_events(
        req: Request,
        _admin: None = Depends(require_admin),
        event: str | None = Query(default=None, max_length=100),
        url: str | None = Query(default=None, max_length=500),
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=200, ge=1, le=1000),
    ) -> list[dict[str, Any]]:
        container = get_container(req)
        return await container.telemetry.rum_service.list_events(
            event=event, url=url, offset=offset, limit=limit
        )

    @router.get(
        "/rum/summary",
        dependencies=(optional_rate_limiter(times=60, seconds=60)),
    )
    async def rum_summary(
        req: Request,
        window: int = Query(default=500, ge=1, le=1000),
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        container = get_container(req)
        return await container.telemetry.rum_service.summary(window)

    @router.get("/summary")
    async def telemetry_summary(
        req: Request, _admin: None = Depends(require_admin)
    ) -> dict[str, Any]:
        container = get_container(req)
        rum = await container.telemetry.rum_service.summary(window=500)
        return {
            "llm": llm_metrics.snapshot(),
            "workers": worker_metrics.snapshot(),
            "events": {
                "counts": event_metrics.snapshot(),
                "handlers": event_metrics.handler_snapshot(),
            },
            "transitions": transition_metrics.snapshot(),
            "ux": ux_metrics.snapshot(),
            "rum": rum,
        }

    def _http_summary_from_registry(top: int = 20) -> dict[str, Any]:
        if REGISTRY is None:
            return {"paths": []}
        reqs: dict[tuple[str, str, str], float] = {}
        d_sum: dict[tuple[str, str], float] = {}
        d_cnt: dict[tuple[str, str], float] = {}
        # Collect samples
        for metric in REGISTRY.collect():  # type: ignore[attr-defined]
            if metric.name == "http_requests_total":
                for sample in metric.samples:
                    method = sample.labels.get("method", "GET")
                    path = sample.labels.get("path", "unknown")
                    status = sample.labels.get("status", "200")
                    reqs[(method, path, status)] = reqs.get(
                        (method, path, status), 0.0
                    ) + float(sample.value)
            elif metric.name == "http_request_duration_ms":
                for sample in metric.samples:
                    if sample.name.endswith("_sum"):
                        method = sample.labels.get("method", "GET")
                        path = sample.labels.get("path", "unknown")
                        d_sum[(method, path)] = float(sample.value)
                    elif sample.name.endswith("_count"):
                        method = sample.labels.get("method", "GET")
                        path = sample.labels.get("path", "unknown")
                        d_cnt[(method, path)] = float(sample.value)
        # Aggregate per (method,path)
        rows: list[dict[str, Any]] = []
        seen_keys: set[tuple[str, str]] = set()
        for method, path, _status in reqs.keys():
            seen_keys.add((method, path))
        for method, path in seen_keys:
            total = 0.0
            err5xx = 0.0
            for (m, p, st), v in reqs.items():
                if m == method and p == path:
                    total += v
                    if st.startswith("5"):
                        err5xx += v
            s = d_sum.get((method, path), 0.0)
            c = d_cnt.get((method, path), 0.0)
            avg = (s / c) if c else 0.0
            rows.append(
                {
                    "method": method,
                    "path": path,
                    "requests_total": total,
                    "error5xx_total": err5xx,
                    "error5xx_ratio": (err5xx / total) if total else 0.0,
                    "avg_duration_ms": avg,
                }
            )
        rows.sort(key=lambda r: r.get("avg_duration_ms", 0.0), reverse=True)
        return {"paths": rows[:top]}

    @router.get("/http/summary")
    async def http_summary(_admin: None = Depends(require_admin)) -> dict[str, Any]:
        return _http_summary_from_registry(top=50)

    @router.get("/llm/summary")
    async def llm_summary(_admin: None = Depends(require_admin)) -> dict[str, Any]:
        return llm_metrics.snapshot()

    @router.get("/workers/summary")
    async def workers_summary(_admin: None = Depends(require_admin)) -> dict[str, Any]:
        return worker_metrics.snapshot()

    @router.get("/events/summary")
    async def events_summary(_admin: None = Depends(require_admin)) -> dict[str, Any]:
        return {
            "counts": event_metrics.snapshot(),
            "handlers": event_metrics.handler_snapshot(),
        }

    @router.get("/transitions/summary")
    async def transitions_summary(
        _admin: None = Depends(require_admin),
    ) -> list[dict[str, Any]]:
        return transition_metrics.snapshot()

    @router.get("/ux/summary")
    async def ux_summary(_admin: None = Depends(require_admin)) -> dict[str, Any]:
        return ux_metrics.snapshot()

    return router
