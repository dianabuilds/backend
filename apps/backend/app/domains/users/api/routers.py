from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.domains.users.application.user_profile_service import UserProfileService
from app.domains.users.infrastructure.models.user import User
from app.domains.users.infrastructure.repositories.user_repository import UserRepository
from app.kernel.db import get_db
from app.schemas.auth import EVMVerify
from app.schemas.user import (
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

