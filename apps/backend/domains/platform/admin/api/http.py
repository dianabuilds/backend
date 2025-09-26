from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from apps.backend import get_container
from domains.platform.iam.security import require_admin


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/admin", tags=["admin"], dependencies=[Depends(require_admin)])

    @router.get("/health")
    async def health() -> dict[str, Any]:
        return {"ok": True}

    @router.get("/readyz")
    async def readyz() -> dict[str, Any]:
        return {"ok": True}

    @router.get("/config")
    async def config(req: Request) -> dict[str, Any]:
        c = get_container(req)
        s = c.settings
        # Redact secrets
        return {
            "env": s.env,
            "database_url": str(s.database_url) if s.database_url else None,
            "redis_url": str(s.redis_url) if s.redis_url else None,
            "event_topics": s.event_topics,
            "event_group": s.event_group,
        }

    return router
