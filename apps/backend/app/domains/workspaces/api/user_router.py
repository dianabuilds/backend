from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.domains.accounts.application.service import (
    AccountService,
    require_account_owner,
)
from app.domains.accounts.infrastructure.models import AccountMember
from app.domains.users.infrastructure.models.user import User
from app.providers.db.session import get_db
from app.schemas.workspaces import WorkspaceIn, WorkspaceOut, WorkspaceUpdate

from ..application.service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("/", response_model=list[WorkspaceOut], summary="List workspaces")
async def list_workspaces(
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> list[WorkspaceOut]:
    rows = await WorkspaceService.list_for_user(db, current_user)
    return [
        WorkspaceOut.model_validate(ws, from_attributes=True).model_copy(update={"role": role})
        for ws, role in rows
    ]


@router.post("", response_model=WorkspaceOut, status_code=201, summary="Create workspace")
async def create_workspace(
    data: WorkspaceIn,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> WorkspaceOut:
    return await AccountService.create(db, data=data, owner=current_user)


@router.patch(
    "/{workspace_id}",
    response_model=WorkspaceOut,
    summary="Update workspace",
)
async def update_workspace(
    workspace_id: int,
    data: WorkspaceUpdate,
    _: Annotated[AccountMember | None, Depends(require_account_owner)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> WorkspaceOut:
    return await AccountService.update(db, workspace_id, data)


@router.delete("/{workspace_id}", status_code=204, summary="Delete workspace")
async def delete_workspace(
    workspace_id: int,
    _: Annotated[AccountMember | None, Depends(require_account_owner)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> Response:
    await AccountService.delete(db, workspace_id)
    return Response(status_code=204)
