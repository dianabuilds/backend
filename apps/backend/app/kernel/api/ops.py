from __future__ import annotations

import json
import os
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.kernel.api.alerts_router import router as alerts_router
from app.kernel.api.cors_router import router as cors_router
from app.kernel.api.overview_router import router as overview_router
from app.domains.admin.api.jobs_router import router as jobs_router
from app.domains.admin.api.audit_router import router as audit_router
from app.kernel.api.health import readyz
from app.kernel.cache_singleton import cache as shared_cache
from app.kernel.db import get_db
from app.domains.auth.security import ADMIN_AUTH_RESPONSES, require_admin_role

admin_required = require_admin_role()

router = APIRouter(
    prefix="/admin/ops",
    tags=["admin"],
    dependencies=[Depends(admin_required)],
    responses=ADMIN_AUTH_RESPONSES,
)

router.include_router(cors_router)
router.include_router(alerts_router)
router.include_router(overview_router)
router.include_router(jobs_router)

CACHE_TTL = 10


def _build_version() -> str:
    return os.getenv("BUILD_VERSION", "dev")


@router.get("/status")
async def get_status(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    cache_key = "ops:status:none"
    cached = await shared_cache.get(cache_key)
    if cached:
        return json.loads(cached)

    ready_resp = await readyz(db)
    ready_data = json.loads(ready_resp.body)

    result = {
        "build": _build_version(),
        "ready": ready_data,
    }
    await shared_cache.set(cache_key, json.dumps(result), CACHE_TTL)
    return result


@router.get("/limits")
async def get_limits(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, int]:
    return {}


__all__ = ["router", "audit_router", "admin_required"]


