from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response

try:
    from fastapi_limiter.depends import RateLimiter  # type: ignore
except Exception:  # pragma: no cover
    RateLimiter = None  # type: ignore

try:  # optional dependency
    from prometheus_client import generate_latest  # type: ignore
except Exception:  # pragma: no cover - optional import
    generate_latest = None  # type: ignore

from apps.backend import get_container
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

    @router.post(
        "/metrics/rum",
        dependencies=(
            [Depends(RateLimiter(times=600, seconds=60))] if RateLimiter else []
        ),
    )
    async def rum_metrics(req: Request) -> dict[str, Any]:
        container = get_container(req)
        payload = await req.json()
        await container.telemetry.rum_service.record(payload)
        return {"ok": True}

    return router
