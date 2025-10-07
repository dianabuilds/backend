from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response

try:  # optional dependency
    from prometheus_client import generate_latest  # type: ignore
except ImportError:  # pragma: no cover - optional import
    generate_latest = None  # type: ignore
try:  # optional dependency
    from fastapi_limiter import FastAPILimiter  # type: ignore
except ImportError:  # pragma: no cover - optional import
    FastAPILimiter = None  # type: ignore

from apps.backend.app.api_gateway.routers import get_container
from domains.platform.telemetry.application.event_metrics_service import (
    event_metrics,
)
from domains.platform.telemetry.application.metrics_registry import (
    llm_metrics,
)
from domains.platform.telemetry.application.transition_metrics_service import (
    transition_metrics,
)
from domains.platform.telemetry.application.ux_metrics_service import (
    ux_metrics,
)
from domains.platform.telemetry.application.worker_metrics_service import (
    worker_metrics,
)
from packages.fastapi_rate_limit import optional_rate_limiter


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1")

    @router.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        if generate_latest is None:
            raise HTTPException(
                status_code=503, detail="prometheus_client not installed"
            )
        text = (
            generate_latest().decode()
            + worker_metrics.prometheus()
            + event_metrics.prometheus()
            + ux_metrics.prometheus()
            + transition_metrics.prometheus()
            + llm_metrics.prometheus()
        )
        return Response(text, media_type="text/plain; version=0.0.4")

    limiter_deps = ()
    if FastAPILimiter is not None and getattr(FastAPILimiter, "redis", None):
        limiter_deps = optional_rate_limiter(times=600, seconds=60)

    @router.post(
        "/metrics/rum",
        dependencies=limiter_deps,
    )
    async def rum_metrics(req: Request) -> dict[str, Any]:
        container = get_container(req)
        payload = await req.json()
        await container.telemetry.rum_service.record(payload)
        return {"ok": True}

    return router
