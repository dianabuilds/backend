from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.health import readyz
from app.core.cache import cache as shared_cache
from app.core.db.session import get_db
from app.domains.workspaces.infrastructure.dao import WorkspaceDAO
from app.schemas.workspaces import WorkspaceSettings
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

admin_required = require_admin_role()

router = APIRouter(
    prefix="/admin/ops",
    tags=["admin"],
    dependencies=[Depends(admin_required)],
    responses=ADMIN_AUTH_RESPONSES,
)

CACHE_TTL = 10


def _build_version() -> str:
    return os.getenv("BUILD_VERSION", "dev")


def _workspace_info(ws: Any) -> dict[str, Any]:
    return {"id": str(ws.id), "slug": ws.slug, "name": ws.name}


@router.get("/status")
async def get_status(
    workspace_id: UUID, db: AsyncSession = Depends(get_db)  # noqa: B008
) -> dict[str, Any]:
    cache_key = f"ops:status:{workspace_id}"
    cached = await shared_cache.get(cache_key)
    if cached:
        return json.loads(cached)

    ws = await WorkspaceDAO.get(db, workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    ready_resp = await readyz(db)
    ready_data = json.loads(ready_resp.body)

    result = {
        "build": _build_version(),
        "workspace": _workspace_info(ws),
        "ready": ready_data,
    }
    await shared_cache.set(cache_key, json.dumps(result), CACHE_TTL)
    return result


@router.get("/limits")
async def get_limits(
    workspace_id: UUID, db: AsyncSession = Depends(get_db)  # noqa: B008
) -> dict[str, int]:
    cache_key = f"ops:limits:{workspace_id}"
    cached = await shared_cache.get(cache_key)
    if cached:
        return json.loads(cached)

    ws = await WorkspaceDAO.get(db, workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    settings = WorkspaceSettings.model_validate(ws.settings_json)
    now = datetime.now(timezone.utc)
    period = now.strftime("%Y%m%d")
    result: dict[str, int] = {}
    for key, limit in settings.limits.items():
        limit_int = int(limit)
        if limit_int <= 0:
            result[key] = -1
            continue
        pattern = f"q:{key}:{period}:*:{workspace_id}"
        keys = await shared_cache.scan(pattern)
        used = 0
        if keys:
            values = await shared_cache.mget(list(keys))
            used = sum(int(v or 0) for v in values)
        remaining = max(limit_int - used, 0)
        result[key] = remaining

    await shared_cache.set(cache_key, json.dumps(result), CACHE_TTL)
    return result
