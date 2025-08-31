from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.db.session import get_db
from app.domains.users.application.user_profile_service import UserProfileService
from app.domains.users.infrastructure.models.user import User
from app.domains.users.infrastructure.repositories.user_repository import UserRepository
from app.schemas.user import UserOut, UserUpdate

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
