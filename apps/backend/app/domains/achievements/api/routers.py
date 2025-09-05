# ruff: noqa: B008, E501
# mypy: ignore-errors
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_workspace, get_current_user
from app.core.db.session import get_db
from app.domains.achievements.application.achievements_service import (
    AchievementsService,
)
from app.domains.achievements.application.admin_service import AchievementsAdminService
from app.domains.achievements.infrastructure.repositories.achievements_repository import (
    AchievementsRepository,
)
from app.domains.users.infrastructure.models.user import User
from app.domains.workspaces.infrastructure.models import Workspace
from app.schemas.achievement import AchievementOut
from app.schemas.achievement_admin import (
    AchievementAdminOut,
    AchievementCreateIn,
    AchievementUpdateIn,
)
from app.security import (
    ADMIN_AUTH_RESPONSES,
    auth_user,
    require_ws_editor,
    require_ws_guest,
)

router = APIRouter()

admin_router = APIRouter(
    prefix="/admin/achievements",
    tags=["admin", "achievements"],
    responses=ADMIN_AUTH_RESPONSES,
)
user_router = APIRouter(prefix="/achievements", tags=["achievements"])


def _admin_svc(db: AsyncSession) -> AchievementsAdminService:
    return AchievementsAdminService(AchievementsRepository(db))


def _svc(db: AsyncSession) -> AchievementsService:
    return AchievementsService(AchievementsRepository(db))


@user_router.get(
    "",
    response_model=list[AchievementOut],
    summary="List achievements",
)
async def list_achievements(
    workspace: Annotated[Workspace, Depends(current_workspace)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    _: Annotated[object, Depends(require_ws_guest)] = ...,
) -> list[AchievementOut]:
    rows = await _svc(db).list(workspace.id, current_user.id)
    items: list[AchievementOut] = []
    for ach, ua in rows:
        items.append(
            AchievementOut(
                id=ach.id,
                code=ach.code,
                title=ach.title,
                description=ach.description,
                icon=ach.icon,
                unlocked=ua is not None,
                unlocked_at=ua.unlocked_at if ua else None,
            )
        )
    return items


@admin_router.get(
    "",
    response_model=list[AchievementAdminOut],
    summary="List achievements (admin)",
)
async def list_achievements_admin(
    workspace_id: UUID,
    workspace: Annotated[Workspace, Depends(current_workspace)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    _: Annotated[object, Depends(require_ws_editor)] = ...,
) -> list[AchievementAdminOut]:
    rows = await _admin_svc(db).list(workspace.id)
    return [AchievementAdminOut.model_validate(r) for r in rows]


@admin_router.post(
    "",
    response_model=AchievementAdminOut,
    summary="Create achievement",
)
async def create_achievement_admin(
    body: AchievementCreateIn,
    workspace_id: UUID,
    workspace: Annotated[Workspace, Depends(current_workspace)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    current: Annotated[User, Depends(auth_user)] = ...,
    _: Annotated[object, Depends(require_ws_editor)] = ...,
) -> AchievementAdminOut:
    data = {
        "code": body.code.strip(),
        "title": body.title.strip(),
        "description": body.description or None,
        "icon": body.icon or None,
        "visible": bool(body.visible),
        "condition": body.condition or {},
    }
    try:
        item = await _admin_svc(db).create(db, workspace.id, data, current.id)
    except ValueError as err:
        if str(err) == "code_conflict":
            raise HTTPException(status_code=409, detail="Code already exists") from err
        raise
    return AchievementAdminOut.model_validate(item)


@admin_router.patch(
    "/{achievement_id}",
    response_model=AchievementAdminOut,
    summary="Update achievement",
)
async def update_achievement_admin(
    achievement_id: UUID,
    body: AchievementUpdateIn,
    workspace_id: UUID,
    workspace: Annotated[Workspace, Depends(current_workspace)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    current: Annotated[User, Depends(auth_user)] = ...,
    _: Annotated[object, Depends(require_ws_editor)] = ...,
) -> AchievementAdminOut:
    data = body.model_dump(exclude_unset=True)
    try:
        item = await _admin_svc(db).update(
            db, workspace.id, achievement_id, data, current.id
        )
    except ValueError as err:
        if str(err) == "code_conflict":
            raise HTTPException(status_code=409, detail="Code already exists") from err
        raise
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return AchievementAdminOut.model_validate(item)


@admin_router.delete("/{achievement_id}", summary="Delete achievement")
async def delete_achievement_admin(
    achievement_id: UUID,
    workspace_id: UUID,
    workspace: Annotated[Workspace, Depends(current_workspace)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    current: Annotated[User, Depends(auth_user)] = ...,
    _: Annotated[object, Depends(require_ws_editor)] = ...,
):
    ok = await _admin_svc(db).delete(db, workspace.id, achievement_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Not found")
    return {"ok": True}


class UserIdIn(BaseModel):
    user_id: UUID


@admin_router.post(
    "/{achievement_id}/grant",
    summary="Grant achievement to user",
)
async def grant_achievement(
    achievement_id: UUID,
    body: UserIdIn,
    workspace_id: UUID,
    workspace: Annotated[Workspace, Depends(current_workspace)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    current: Annotated[User, Depends(auth_user)] = ...,
    _: Annotated[object, Depends(require_ws_editor)] = ...,
):
    granted = await _svc(db).grant_manual(
        db, workspace.id, body.user_id, achievement_id
    )
    return {"granted": granted}


@admin_router.post(
    "/{achievement_id}/revoke",
    summary="Revoke achievement from user",
)
async def revoke_achievement(
    achievement_id: UUID,
    body: UserIdIn,
    workspace_id: UUID,
    workspace: Annotated[Workspace, Depends(current_workspace)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    current: Annotated[User, Depends(auth_user)] = ...,
    _: Annotated[object, Depends(require_ws_editor)] = ...,
):
    revoked = await _svc(db).revoke_manual(
        db, workspace.id, body.user_id, achievement_id
    )
    return {"revoked": revoked}


router.include_router(user_router)
router.include_router(admin_router)
