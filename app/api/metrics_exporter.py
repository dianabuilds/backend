from __future__ import annotations

from fastapi import APIRouter, Response, HTTPException

from app.core.config import settings
from app.core.metrics import metrics_storage

router = APIRouter()


@router.get(settings.observability.metrics_path, include_in_schema=False)
async def metrics() -> Response:
    if not settings.observability.metrics_enabled:
        raise HTTPException(status_code=404)
    text = metrics_storage.prometheus()
    return Response(text, media_type="text/plain; version=0.0.4")
