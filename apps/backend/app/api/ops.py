from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.ops.alerts import router as alerts_router
from app.admin.ops.cors import router as cors_router
from app.api.health import readyz
from app.core.cache import cache as shared_cache
from app.domains.workspaces.infrastructure.dao import WorkspaceDAO
from app.domains.workspaces.infrastructure.models import Workspace
from app.providers.db.session import get_db
from app.schemas.workspaces import WorkspaceSettings
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

admin_required = require_admin_role()

router = APIRouter(
    prefix="/admin/ops",
    tags=["admin"],
    dependencies=[Depends(admin_required)],
    responses=ADMIN_AUTH_RESPONSES,
)

router.include_router(cors_router)
router.include_router(alerts_router)

CACHE_TTL = 10


def _build_version() -> str:
    return os.getenv("BUILD_VERSION", "dev")


def _workspace_info(ws: Any) -> dict[str, Any]:
    return {"id": str(ws.id), "slug": ws.slug, "name": ws.name}


async def _resolve_workspace(
    db: AsyncSession, workspace_id: UUID | None
) -> Workspace | None:
    if workspace_id:
        return await WorkspaceDAO.get(db, workspace_id)
    # попробуем системный workspace 'main'
    res = await db.execute(select(Workspace).where(Workspace.slug == "main"))
    ws = res.scalars().first()
    if ws:
        return ws
    # fallback: первый существующий
    res = await db.execute(select(Workspace).order_by(Workspace.created_at))
    return res.scalars().first()


@router.get("/status")
async def get_status(
    db: Annotated[AsyncSession, Depends(get_db)],
    workspace_id: UUID | None = None,
) -> dict[str, Any]:
    # Кэшируем по реальному id (или по ключу 'none', если WS не найден)
    ws = await _resolve_workspace(db, workspace_id)
    cache_ws_key = str(ws.id) if ws else "none"
    cache_key = f"ops:status:{cache_ws_key}"
    cached = await shared_cache.get(cache_key)
    if cached:
        return json.loads(cached)

    ready_resp = await readyz(db)
    ready_data = json.loads(ready_resp.body)

    result = {
        "build": _build_version(),
        "workspace": _workspace_info(ws) if ws else None,
        "ready": ready_data,
    }
    await shared_cache.set(cache_key, json.dumps(result), CACHE_TTL)
    return result


@router.get("/limits")
async def get_limits(
    db: Annotated[AsyncSession, Depends(get_db)],
    workspace_id: UUID | None = None,
) -> dict[str, int]:
    ws = await _resolve_workspace(db, workspace_id)
    if not ws:
        # нет рабочей области — вернём пустые лимиты, но не валимся
        return {}

    cache_key = f"ops:limits:{ws.id}"
    cached = await shared_cache.get(cache_key)
    if cached:
        return json.loads(cached)

    settings = WorkspaceSettings.model_validate(ws.settings_json)
    now = datetime.now(UTC)
    period = now.strftime("%Y%m%d")
    result: dict[str, int] = {}
    for key, limit in settings.limits.items():
        limit_int = int(limit)
        if limit_int <= 0:
            result[key] = -1
            continue
        pattern = f"q:{key}:{period}:*:{ws.id}"
        keys = await shared_cache.scan(pattern)
        used = 0
        if keys:
            values = await shared_cache.mget(list(keys))
            used = sum(int(v or 0) for v in values)
        remaining = max(limit_int - used, 0)
        result[key] = remaining

    await shared_cache.set(cache_key, json.dumps(result), CACHE_TTL)
    return result
