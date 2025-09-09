from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.domains.users.application.profile_service import ProfileService
from app.domains.users.application.user_profile_service import UserProfileService
from app.domains.users.infrastructure.models.user import User
from app.domains.users.infrastructure.models.user_profile import UserProfile
from app.domains.users.infrastructure.repositories.user_profile_repository import (
    UserProfileRepository,
)
from app.domains.users.infrastructure.repositories.user_repository import UserRepository
from app.providers.db.session import get_db
from app.schemas.user import (
    UserOut,
    UserUpdate,
)
from app.schemas.user_profile import (
    UserProfileOut,
    UserProfileUpdate,
    UserSettingsOut,
    UserSettingsUpdate,
)
from config.feature_flags import feature_flags

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


@router.get("/me/profile", response_model=UserProfileOut, summary="My profile")
async def read_my_profile(
        current_user: Annotated[User, Depends(get_current_user)] = ...,
        db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> UserProfile:
    if not feature_flags.profile_enabled:
        raise HTTPException(status_code=404, detail="Not found")
    service = ProfileService(UserProfileRepository(db))
    return await service.get_profile(current_user.id)


@router.patch(
    "/me/profile",
    response_model=UserProfileOut,
    summary="Update my profile",
)
async def update_my_profile(
        payload: UserProfileUpdate,
        current_user: Annotated[User, Depends(get_current_user)] = ...,
        db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> UserProfile:
    if not feature_flags.profile_enabled:
        raise HTTPException(status_code=404, detail="Not found")
    service = ProfileService(UserProfileRepository(db))
    data = payload.model_dump(exclude_unset=True)
    return await service.update_profile(current_user.id, data)


@router.get(
    "/me/settings",
    response_model=UserSettingsOut,
    summary="My settings",
)
async def read_my_settings(
        current_user: Annotated[User, Depends(get_current_user)] = ...,
        db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> dict:
    if not feature_flags.profile_enabled:
        raise HTTPException(status_code=404, detail="Not found")
    service = ProfileService(UserProfileRepository(db))
    return await service.get_settings(current_user.id)


@router.patch(
    "/me/settings",
    response_model=UserSettingsOut,
    summary="Update my settings",
)
async def update_my_settings(
        payload: UserSettingsUpdate,
        current_user: Annotated[User, Depends(get_current_user)] = ...,
        db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> dict:
    if not feature_flags.profile_enabled:
        raise HTTPException(status_code=404, detail="Not found")
    service = ProfileService(UserProfileRepository(db))
    return await service.update_settings(current_user.id, payload.preferences)


@router.delete("/me", summary="Delete account")
async def delete_me(
        current_user: Annotated[User, Depends(get_current_user)] = ...,
        db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> dict:
    service = UserProfileService(UserRepository(db))
    return await service.delete_me(current_user)


@router.get("/{user_id}/profile", response_model=UserProfileOut, summary="User profile")
async def read_user_profile(
        user_id: UUID,
        db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> UserProfile:
    if not feature_flags.profile_enabled:
        raise HTTPException(status_code=404, detail="Not found")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Not found")
    service = ProfileService(UserProfileRepository(db))
    return await service.get_profile(user_id)
