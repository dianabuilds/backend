from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.profile.application.policies import can_read_profile, can_update_profile
from app.domains.profile.application.services.profile_service import ProfileService
from app.domains.profile.infrastructure.repositories.profile_repo import (
    ProfileRepository,
    UsernameAlreadyExists,
)
from app.kernel.db import get_db
from app.api.deps import get_current_user, get_current_user_optional
from app.domains.users.infrastructure.models.user import User
from app.domains.profile.events.publisher import publish_profile_updated
from app.schemas.profile import (
    ProfileOut,
    ProfileSettingsOut,
    ProfileSettingsUpdate,
    ProfileUpdate,
)

router = APIRouter(prefix="/profile", tags=["Profile"])


def get_service(db: AsyncSession = Depends(get_db)) -> ProfileService:
    return ProfileService(ProfileRepository(db))


@router.get("/{user_id}", response_model=ProfileOut)
async def get_profile(
    user_id: UUID,
    svc: ProfileService = Depends(get_service),
    current_user: User | None = Depends(get_current_user_optional),
    request: Request | None = None,
    response: Response | None = None,
) -> dict:
    data = await svc.get(user_id)
    if not data:
        raise HTTPException(status_code=404, detail="profile not found")
    subject_id = current_user.id if current_user else None
    if not can_read_profile(subject_id, user_id):
        raise HTTPException(status_code=403, detail="forbidden")
    # Simple weak ETag based on stable JSON representation
    try:
        import json, hashlib

        etag = hashlib.md5(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()
        if request is not None:
            inm = request.headers.get("if-none-match") or request.headers.get("If-None-Match")
            if inm and inm == etag:
                assert response is not None
                response.status_code = 304
                return {}
        if response is not None:
            response.headers["ETag"] = etag
    except Exception:
        pass
    return data


@router.patch("/{user_id}", response_model=ProfileOut)
async def patch_profile(
    user_id: UUID,
    payload: ProfileUpdate,
    svc: ProfileService = Depends(get_service),
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> dict:
    subject_id = current_user.id if current_user else None
    if not can_update_profile(subject_id, user_id):
        raise HTTPException(status_code=403, detail="forbidden")
    try:
        res = await svc.update(user_id, payload.model_dump(exclude_unset=True))
    except UsernameAlreadyExists:
        raise HTTPException(status_code=409, detail="username already exists")
    try:
        await publish_profile_updated(db, profile=res)
    except Exception:
        # avoid failing user request on event enqueue issues
        pass
    return res

__all__ = ["router"]


# Convenience endpoints using auth context
@router.get("/me", response_model=ProfileOut)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    svc: ProfileService = Depends(get_service),
    request: Request | None = None,
    response: Response | None = None,
):
    data = await svc.get(current_user.id)
    if not data:
        raise HTTPException(status_code=404, detail="profile not found")
    # ETag for /me as well
    try:
        import json, hashlib

        etag = hashlib.md5(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()
        if request is not None:
            inm = request.headers.get("if-none-match") or request.headers.get("If-None-Match")
            if inm and inm == etag:
                assert response is not None
                response.status_code = 304
                return {}
        if response is not None:
            response.headers["ETag"] = etag
    except Exception:
        pass
    return data


@router.patch("/me", response_model=ProfileOut)
async def patch_my_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    svc: ProfileService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    try:
        res = await svc.update(current_user.id, payload.model_dump(exclude_unset=True))
    except UsernameAlreadyExists:
        raise HTTPException(status_code=409, detail="username already exists")
    try:
        await publish_profile_updated(db, profile=res)
    except Exception:
        pass
    return res


@router.get("/me/settings", response_model=ProfileSettingsOut)
async def get_my_settings(current_user: User = Depends(get_current_user), svc: ProfileService = Depends(get_service)):
    return await svc.get_settings(current_user.id)


@router.patch("/me/settings", response_model=ProfileSettingsOut)
async def patch_my_settings(
    payload: ProfileSettingsUpdate,
    current_user: User = Depends(get_current_user),
    svc: ProfileService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    res = await svc.update_settings(current_user.id, payload.preferences)
    try:
        await publish_profile_updated(db, profile=res)
    except Exception:
        pass
    return res

