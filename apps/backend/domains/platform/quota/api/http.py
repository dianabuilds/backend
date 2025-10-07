from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

try:
    from prometheus_client import Counter  # type: ignore
except ImportError:  # pragma: no cover
    Counter = None  # type: ignore

logger = logging.getLogger(__name__)

QUOTA_HIT = (
    Counter("quota_hit_total", "Total quota rejections", labelnames=("key", "scope"))
    if Counter is not None
    else None
)

from apps.backend.app.api_gateway.routers import get_container
from domains.platform.iam.security import require_admin
from packages.fastapi_rate_limit import optional_rate_limiter

from .schemas import QuotaConsumeIn, QuotaConsumeOut


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/quota", tags=["quota"])

    @router.post(
        "/consume",
        response_model=QuotaConsumeOut,
        dependencies=(optional_rate_limiter(times=120, seconds=60)),
    )
    async def consume(
        req: Request, body: QuotaConsumeIn, _admin: None = Depends(require_admin)
    ) -> dict[str, Any]:
        container = get_container(req)
        res = await container.quota.service.consume(
            user_id=body.user_id,
            key=body.key,
            limit=body.limit,
            amount=body.amount,
            scope=body.scope,
        )
        out = asdict(res)
        if not res.allowed:
            if QUOTA_HIT is not None:
                try:
                    QUOTA_HIT.labels(key=body.key, scope=body.scope).inc()
                except (ValueError, RuntimeError) as exc:
                    logger.debug(
                        "quota metrics increment failed for key=%s scope=%s: %s",
                        body.key,
                        body.scope,
                        exc,
                    )
            raise HTTPException(
                status_code=429, detail={"code": "QUOTA_EXCEEDED", **out}
            )
        return out

    return router
