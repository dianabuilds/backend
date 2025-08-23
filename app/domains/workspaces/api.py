from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.db.session import get_db
from app.schemas.workspaces import (
    WorkspaceIn,
    WorkspaceOut,
    WorkspaceWithRoleOut,
    WorkspaceUpdate,
    WorkspaceMemberIn,
    WorkspaceMemberOut,
)
from app.security import (
    ADMIN_AUTH_RESPONSES,
    auth_user,
    require_ws_editor,
    require_ws_owner,
)
from app.domains.workspaces.infrastructure.models import Workspace, WorkspaceMember
from app.domains.workspaces.application.service import WorkspaceService
from app.domains.users.infrastructure.models.user import User

router = APIRouter(
    prefix="/admin/workspaces",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.post("", response_model=WorkspaceOut, status_code=201, summary="Create workspace")
async def create_workspace(
    data: WorkspaceIn,
    user: User = Depends(auth_user),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceOut:
    workspace = await WorkspaceService.create(db, data=data, owner=user)
    return workspace


@router.get("", response_model=list[WorkspaceWithRoleOut], summary="List workspaces")
async def list_workspaces(
    user: User = Depends(auth_user),
    db: AsyncSession = Depends(get_db),
) -> list[WorkspaceWithRoleOut]:
    stmt = (
        select(Workspace, WorkspaceMember.role)
        .join(WorkspaceMember)
        .where(WorkspaceMember.user_id == user.id)
    )
    result = await db.execute(stmt)
    workspaces: list[WorkspaceWithRoleOut] = []
    for ws, role in result.all():
        data = WorkspaceOut.model_validate(ws, from_attributes=True)
        workspaces.append(
            WorkspaceWithRoleOut(**data.model_dump(), role=role)
        )
    return workspaces


@router.get("/{workspace_id}", response_model=WorkspaceOut, summary="Get workspace")
async def get_workspace(
    workspace_id: UUID,
    user: User = Depends(auth_user),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceOut:
    return await WorkspaceService.get_for_user(db, workspace_id, user)


@router.patch("/{workspace_id}", response_model=WorkspaceOut, summary="Update workspace")
async def update_workspace(
    workspace_id: UUID,
    data: WorkspaceUpdate,
    _: WorkspaceMember | None = Depends(require_ws_editor),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceOut:
    return await WorkspaceService.update(db, workspace_id, data)


@router.delete("/{workspace_id}", status_code=204, summary="Delete workspace")
async def delete_workspace(
    workspace_id: UUID,
    _: WorkspaceMember | None = Depends(require_ws_owner),
    db: AsyncSession = Depends(get_db),
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
    _: WorkspaceMember | None = Depends(require_ws_owner),
    db: AsyncSession = Depends(get_db),
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
    _: WorkspaceMember | None = Depends(require_ws_owner),
    db: AsyncSession = Depends(get_db),
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
    _: WorkspaceMember | None = Depends(require_ws_owner),
    db: AsyncSession = Depends(get_db),
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
    _: WorkspaceMember | None = Depends(require_ws_owner),
    db: AsyncSession = Depends(get_db),
) -> list[WorkspaceMemberOut]:
    return await WorkspaceService.list_members(db, workspace_id)
