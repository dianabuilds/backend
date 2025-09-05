from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.domains.users.application.user_profile_service import UserProfileService
from app.domains.users.infrastructure.models.user import User
from app.domains.users.infrastructure.repositories.user_repository import UserRepository
from app.domains.workspaces.infrastructure.dao import WorkspaceDAO, WorkspaceMemberDAO
from app.providers.db.session import get_db
from app.schemas.user import (
    UserDefaultWorkspaceUpdate,
    UserOut,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut, summary="Current user")
async def read_me(
    current_user: Annotated[User, Depends(get_current_user)] = ...,
) -> User:
    service = UserProfileService(UserRepository(None))  # repo не нужен для read
    return await service.read_me(current_user)


@router.patch("/me", response_model=UserOut, summary="Update profile")
async def update_me(
    payload: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> User:
    service = UserProfileService(UserRepository(db))
    data = payload.model_dump(exclude_unset=True)
    return await service.update_me(current_user, data)


@router.delete("/me", summary="Delete account")
async def delete_me(
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> dict:
    service = UserProfileService(UserRepository(db))
    return await service.delete_me(current_user)


@router.patch(
    "/me/default-workspace",
    response_model=UserOut,
    summary="Set default workspace",
)
async def set_default_workspace(
    payload: UserDefaultWorkspaceUpdate,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> User:
    workspace_id = payload.default_workspace_id
    if workspace_id is not None:
        workspace = await WorkspaceDAO.get(db, workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        if current_user.role != "admin":
            member = await WorkspaceMemberDAO.get(
                db, workspace_id=workspace_id, user_id=current_user.id
            )
            if not member:
                raise HTTPException(status_code=403, detail="Forbidden")
    service = UserProfileService(UserRepository(db))
    return await service.update_default_workspace(current_user, workspace_id)
