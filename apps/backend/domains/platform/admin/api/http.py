from __future__ import annotations

from fastapi import APIRouter, Depends

from domains.platform.iam.security import require_admin

from .endpoints import config, health, integrations, system


def make_router() -> APIRouter:
    router = APIRouter(
        prefix="/v1/admin", tags=["admin"], dependencies=[Depends(require_admin)]
    )
    health.register(router)
    config.register(router)
    integrations.register(router)
    system.register(router)
    return router
