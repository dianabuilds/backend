from __future__ import annotations

import csv
import io
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.infrastructure.repositories.usage_repository import (
    AIUsageRepository,
)
from app.domains.workspaces.infrastructure.dao import WorkspaceDAO
from app.providers.db.session import get_db
from app.schemas.workspaces import WorkspaceSettings
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

admin_required = require_admin_role({"admin"})

router = APIRouter(
    prefix="/admin/ai/usage",
    tags=["admin-ai-usage"],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.get("/system", summary="System-wide usage totals")
async def get_system_usage(
    _: Annotated[object, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> dict:
    repo = AIUsageRepository(db)
    return await repo.system_totals()


@router.get("/workspaces", summary="Usage by workspace", response_model=None)
async def get_usage_by_workspace(
    format: Annotated[str | None, Query()] = None,
    _: Annotated[object, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    repo = AIUsageRepository(db)
    rows = await repo.by_workspace()
    # attach limits for progress bar
    out: list[dict] = []
    for r in rows:
        ws = await WorkspaceDAO.get(db, r["workspace_id"])
        limit = 0
        if ws:
            settings = WorkspaceSettings.model_validate(ws.settings_json)
            limit = int(settings.limits.get("ai_tokens", 0))
        progress = r["tokens"] / limit if limit else 0
        out.append({**r, "limit": limit, "progress": progress})
    if format == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["workspace_id", "tokens", "cost", "limit", "progress"])
        for r in out:
            writer.writerow(
                [r["workspace_id"], r["tokens"], r["cost"], r["limit"], r["progress"]]
            )
        return Response(buf.getvalue(), media_type="text/csv")
    return out


@router.get(
    "/workspaces/{workspace_id}/users",
    summary="Usage by user in workspace",
    response_model=None,
)
async def get_usage_by_user(
    workspace_id: UUID,
    format: Annotated[str | None, Query()] = None,
    _: Annotated[object, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    repo = AIUsageRepository(db)
    rows = await repo.by_user(workspace_id)
    if format == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["user_id", "tokens", "cost"])
        for r in rows:
            writer.writerow([r["user_id"], r["tokens"], r["cost"]])
        return Response(buf.getvalue(), media_type="text/csv")
    return rows


@router.get(
    "/workspaces/{workspace_id}/models",
    summary="Usage by model in workspace",
    response_model=None,
)
async def get_usage_by_model(
    workspace_id: UUID,
    format: Annotated[str | None, Query()] = None,
    _: Annotated[object, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    repo = AIUsageRepository(db)
    rows = await repo.by_model(workspace_id)
    if format == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["model", "tokens", "cost"])
        for r in rows:
            writer.writerow([r["model"], r["tokens"], r["cost"]])
        return Response(buf.getvalue(), media_type="text/csv")
    return rows
