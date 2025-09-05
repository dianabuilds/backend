from __future__ import annotations

from collections.abc import Mapping

# ruff: noqa: B008
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from jsonschema import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.core.pagination import parse_page_query
from app.domains.ai.infrastructure.repositories.usage_repository import (
    AIUsageRepository,
)
from app.domains.notifications.application.notify_service import NotifyService
from app.domains.notifications.infrastructure.repositories import (
    notification_repository,
)
from app.domains.notifications.infrastructure.transports.websocket import (
    WebsocketPusher,
)
from app.domains.notifications.infrastructure.transports.websocket import (
    manager as ws_manager,
)
from app.domains.notifications.validation import validate_notification_rules
from app.domains.users.infrastructure.models.user import User
from app.domains.workspaces.application.service import WorkspaceService
from app.domains.workspaces.infrastructure.dao import WorkspaceDAO
from app.domains.workspaces.infrastructure.models import WorkspaceMember
from app.schemas.notification import NotificationType
from app.schemas.notification_rules import NotificationRules
from app.schemas.workspaces import (
    WorkspaceCursorPage,
    WorkspaceIn,
    WorkspaceMemberIn,
    WorkspaceMemberOut,
    WorkspaceOut,
    WorkspaceSettings,
    WorkspaceUpdate,
)
from app.security import (
    ADMIN_AUTH_RESPONSES,
    auth_user,
    require_ws_editor,
    require_ws_owner,
    require_ws_viewer,
)

router = APIRouter(
    prefix="/admin/workspaces",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.post(
    "", response_model=WorkspaceOut, status_code=201, summary="Create workspace"
)
async def create_workspace(
    data: WorkspaceIn,
    user: Annotated[User, Depends(auth_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> WorkspaceOut:
    workspace = await WorkspaceService.create(db, data=data, owner=user)
    return workspace


@router.get("", response_model=WorkspaceCursorPage, summary="List workspaces")
async def list_workspaces(
    request: Request,
    user: Annotated[User, Depends(auth_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> WorkspaceCursorPage:
    params: Mapping[str, str] = dict(request.query_params)
    pq = parse_page_query(
        params,
        allowed_sort=["created_at"],
        default_sort="created_at",
    )
    return await WorkspaceService.list_paginated(db, user=user, pq=pq)


@router.get("/{workspace_id}", response_model=WorkspaceOut, summary="Get workspace")
async def get_workspace(
    workspace_id: UUID,
    user: Annotated[User, Depends(auth_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> WorkspaceOut:
    return await WorkspaceService.get_for_user(db, workspace_id, user)


@router.patch(
    "/{workspace_id}", response_model=WorkspaceOut, summary="Update workspace"
)
async def update_workspace(
    workspace_id: UUID,
    data: WorkspaceUpdate,
    _: Annotated[WorkspaceMember | None, Depends(require_ws_editor)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> WorkspaceOut:
    return await WorkspaceService.update(db, workspace_id, data)


@router.delete("/{workspace_id}", status_code=204, summary="Delete workspace")
async def delete_workspace(
    workspace_id: UUID,
    _: Annotated[WorkspaceMember | None, Depends(require_ws_owner)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> Response:
    await WorkspaceService.delete(db, workspace_id)
    return Response(status_code=204)


@router.post(
    "/{workspace_id}/members",
    response_model=WorkspaceMemberOut,
    status_code=201,
    summary="Add workspace member",
)
async def add_member(
    workspace_id: UUID,
    data: WorkspaceMemberIn,
    _: Annotated[WorkspaceMember | None, Depends(require_ws_owner)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> WorkspaceMemberOut:
    return await WorkspaceService.add_member(db, workspace_id, data)


@router.patch(
    "/{workspace_id}/members/{user_id}",
    response_model=WorkspaceMemberOut,
    summary="Update workspace member",
)
async def update_member(
    workspace_id: UUID,
    user_id: UUID,
    data: WorkspaceMemberIn,
    _: Annotated[WorkspaceMember | None, Depends(require_ws_owner)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> WorkspaceMemberOut:
    if data.user_id != user_id:
        raise HTTPException(status_code=400, detail="User ID mismatch")
    return await WorkspaceService.update_member(db, workspace_id, user_id, data.role)


@router.delete(
    "/{workspace_id}/members/{user_id}",
    status_code=204,
    summary="Remove workspace member",
)
async def remove_member(
    workspace_id: UUID,
    user_id: UUID,
    _: Annotated[WorkspaceMember | None, Depends(require_ws_owner)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> Response:
    await WorkspaceService.remove_member(db, workspace_id, user_id)
    return Response(status_code=204)


@router.get(
    "/{workspace_id}/members",
    response_model=list[WorkspaceMemberOut],
    summary="List workspace members",
)
async def list_members(
    workspace_id: UUID,
    _: Annotated[WorkspaceMember | None, Depends(require_ws_owner)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> list[WorkspaceMemberOut]:
    return await WorkspaceService.list_members(db, workspace_id)


@router.get(
    "/{workspace_id}/settings/ai-presets",
    response_model=dict[str, Any],
    summary="Get workspace AI presets",
)
async def get_ai_presets(
    workspace_id: UUID,
    _: Annotated[WorkspaceMember | None, Depends(require_ws_editor)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> dict[str, Any]:
    workspace = await WorkspaceDAO.get(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    settings = WorkspaceSettings.model_validate(workspace.settings_json)
    return settings.ai_presets


@router.put(
    "/{workspace_id}/settings/ai-presets",
    response_model=dict[str, Any],
    summary="Update workspace AI presets",
)
async def put_ai_presets(
    workspace_id: UUID,
    presets: dict[str, Any],
    _: Annotated[WorkspaceMember | None, Depends(require_ws_editor)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> dict[str, Any]:
    workspace = await WorkspaceDAO.get(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    try:
        from app.domains.ai.validation import validate_ai_presets

        validate_ai_presets(presets)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    settings = WorkspaceSettings.model_validate(workspace.settings_json)
    settings.ai_presets = presets
    workspace.settings_json = settings.model_dump()
    await db.commit()
    await db.refresh(workspace)
    return settings.ai_presets


@router.get(
    "/{workspace_id}/settings/notifications",
    response_model=NotificationRules,
    summary="Get workspace notification rules",
)
async def get_notifications(
    workspace_id: UUID,
    _: Annotated[WorkspaceMember | None, Depends(require_ws_editor)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> NotificationRules:
    workspace = await WorkspaceDAO.get(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    settings = WorkspaceSettings.model_validate(workspace.settings_json)
    return settings.notifications


@router.put(
    "/{workspace_id}/settings/notifications",
    response_model=NotificationRules,
    summary="Update workspace notification rules",
)
async def put_notifications(
    workspace_id: UUID,
    rules: NotificationRules,
    _: Annotated[WorkspaceMember | None, Depends(require_ws_editor)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> NotificationRules:
    workspace = await WorkspaceDAO.get(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    # Validate explicitly
    _ = validate_notification_rules(rules.model_dump())
    settings = WorkspaceSettings.model_validate(workspace.settings_json)
    settings.notifications = rules
    workspace.settings_json = settings.model_dump()
    await db.commit()
    await db.refresh(workspace)
    return settings.notifications


@router.get(
    "/{workspace_id}/settings/limits",
    response_model=dict[str, int],
    summary="Get workspace limits",
)
async def get_limits(
    workspace_id: UUID,
    _: Annotated[WorkspaceMember | None, Depends(require_ws_editor)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> dict[str, int]:
    workspace = await WorkspaceDAO.get(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    settings = WorkspaceSettings.model_validate(workspace.settings_json)
    return settings.limits


@router.put(
    "/{workspace_id}/settings/limits",
    response_model=dict[str, int],
    summary="Update workspace limits",
)
async def put_limits(
    workspace_id: UUID,
    limits: dict[str, int],
    _: Annotated[WorkspaceMember | None, Depends(require_ws_editor)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> dict[str, int]:
    workspace = await WorkspaceDAO.get(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    settings = WorkspaceSettings.model_validate(workspace.settings_json)
    settings.limits = limits
    workspace.settings_json = settings.model_dump()
    await db.commit()
    await db.refresh(workspace)
    return settings.limits


@router.get(
    "/{workspace_id}/usage",
    summary="Get workspace AI usage",
)
async def get_workspace_usage(
    workspace_id: UUID,
    user: Annotated[User, Depends(auth_user)] = ...,
    _: Annotated[WorkspaceMember | None, Depends(require_ws_viewer)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> dict:
    repo = AIUsageRepository(db)
    totals = await repo.workspace_totals(workspace_id)
    workspace = await WorkspaceDAO.get(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    settings = WorkspaceSettings.model_validate(workspace.settings_json)
    limit = int(settings.limits.get("ai_tokens", 0))
    tokens = int(totals["tokens"])
    progress = tokens / limit if limit else 0
    alert: str | None = None
    if limit:
        ratio = tokens / limit
        if ratio >= 1:
            alert = "quota_exceeded"
        elif ratio >= 0.8:
            alert = "quota_warning"
    if alert:
        try:
            notify = NotifyService(
                notification_repository.NotificationRepository(db),
                WebsocketPusher(ws_manager),
            )
            await notify.create_notification(
                workspace_id=workspace_id,
                user_id=user.id,
                title="AI quota alert",
                message=f"AI token usage {tokens}/{limit}",
                type=NotificationType.system,
            )
        except Exception:
            pass
    return {
        "workspace_id": workspace_id,
        "tokens": tokens,
        "cost": float(totals["cost"]),
        "limit": limit,
        "progress": progress,
        "alert": alert,
    }
