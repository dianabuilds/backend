from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response
from prometheus_client import generate_latest

from app.core.config import settings
from app.core.metrics import metrics_storage
from app.domains.telemetry.application.event_metrics_facade import event_metrics
from app.domains.telemetry.application.metrics_registry import llm_metrics
from app.domains.telemetry.application.transition_metrics_facade import (
    transition_metrics,
)
from app.domains.telemetry.application.worker_metrics_facade import worker_metrics

router = APIRouter()


@router.get(settings.observability.metrics_path, include_in_schema=False)
async def metrics() -> Response:
    if not settings.observability.metrics_enabled:
        raise HTTPException(status_code=404)
    text = (
        generate_latest().decode()
        + metrics_storage.prometheus()
        + llm_metrics.prometheus()
        + worker_metrics.prometheus()
        + event_metrics.prometheus()
        + transition_metrics.prometheus()
    )
    return Response(text, media_type="text/plain; version=0.0.4")
