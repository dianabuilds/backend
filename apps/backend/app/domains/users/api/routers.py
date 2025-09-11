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
from app.schemas.auth import EVMVerify
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

# Feature flags import: prefer local "config" if available, otherwise import via
# fully-qualified package path when running from the repository root.
try:  # pragma: no cover - environment-dependent import path
    from config.feature_flags import feature_flags  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    from apps.backend.config.feature_flags import feature_flags  # type: ignore

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


@router.post("/me/wallets/siwe-nonce", summary="Create SIWE nonce")
async def wallet_siwe_nonce(
    current_user: Annotated[User, Depends(get_current_user)] = ...,
):
    # Reuse auth service nonce store via auth router module-level instance
    # Generate and store nonce keyed by user id
    from uuid import uuid4

    from app.domains.auth.api.auth_router import _nonce_store  # lazy import to avoid circulars

    value = uuid4().hex
    await _nonce_store.set(str(current_user.id), value)
    return {"nonce": value}


@router.post("/me/wallets/siwe-verify", summary="Verify SIWE and link wallet")
async def wallet_siwe_verify(
    payload: EVMVerify,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    # Pop nonce stored for this user and compare with provided message
    from app.domains.auth.api.auth_router import _nonce_store  # reuse redis store

    stored = await _nonce_store.pop(str(current_user.id))
    if not stored or stored != payload.message:
        raise HTTPException(status_code=400, detail="Invalid nonce")

    # Link wallet on profile
    current_user.wallet_address = payload.wallet_address
    await db.commit()
    await db.refresh(current_user)
    return {"wallet_address": current_user.wallet_address}


@router.post("/me/wallets/unlink", summary="Unlink wallet from profile")
async def wallet_unlink(
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    current_user.wallet_address = None
    await db.commit()
    await db.refresh(current_user)
    return {"wallet_address": None}
