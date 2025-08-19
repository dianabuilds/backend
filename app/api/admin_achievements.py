from __future__ import annotations

from typing import List, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.db.session import get_db
from app.models.user import User
from app.models.achievement import Achievement
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role
from app.services.achievements import AchievementsService
from app.schemas.achievement_admin import (
    AchievementAdminOut,
    AchievementCreateIn,
    AchievementUpdateIn,
)

admin_required = require_admin_role()

router = APIRouter(
    prefix="/admin/achievements",
    tags=["admin", "achievements"],
    dependencies=[Depends(admin_required)],
    responses=ADMIN_AUTH_RESPONSES,
)


# ---- CRUD ----

@router.get("", response_model=List[AchievementAdminOut], summary="List achievements (admin)")
async def list_achievements_admin(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_required),
) -> List[AchievementAdminOut]:
    res = await db.execute(select(Achievement).order_by(Achievement.title.asc()))
    rows = list(res.scalars().all())
    return [AchievementAdminOut.model_validate(r) for r in rows]


@router.post("", response_model=AchievementAdminOut, summary="Create achievement")
async def create_achievement_admin(
    body: AchievementCreateIn,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_required),
) -> AchievementAdminOut:
    # уникальность кода
    exists = await db.execute(select(Achievement).where(Achievement.code == body.code))
    if exists.scalars().first():
        raise HTTPException(status_code=409, detail="Code already exists")
    item = Achievement(
        code=body.code.strip(),
        title=body.title.strip(),
        description=(body.description or None),
        icon=(body.icon or None),
        visible=bool(body.visible),
        condition=body.condition or {},
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return AchievementAdminOut.model_validate(item)


@router.patch("/{achievement_id}", response_model=AchievementAdminOut, summary="Update achievement")
async def update_achievement_admin(
    achievement_id: UUID,
    body: AchievementUpdateIn,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_required),
) -> AchievementAdminOut:
    item = await db.get(Achievement, achievement_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if body.code is not None:
        # проверка уникальности кода при изменении
        if body.code != item.code:
            exists = await db.execute(select(Achievement).where(Achievement.code == body.code))
            if exists.scalars().first():
                raise HTTPException(status_code=409, detail="Code already exists")
        item.code = body.code.strip()
    if body.title is not None:
        item.title = body.title.strip()
    if body.description is not None:
        item.description = body.description or None
    if body.icon is not None:
        item.icon = body.icon or None
    if body.visible is not None:
        item.visible = bool(body.visible)
    if body.condition is not None:
        item.condition = body.condition
    await db.commit()
    await db.refresh(item)
    return AchievementAdminOut.model_validate(item)


@router.delete("/{achievement_id}", summary="Delete achievement")
async def delete_achievement_admin(
    achievement_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_required),
):
    item = await db.get(Achievement, achievement_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(item)
    await db.commit()
    return {"ok": True}


# ---- grant/revoke to users ----

class GrantRequest(BaseModel):
    user_id: UUID


class RevokeRequest(BaseModel):
    user_id: UUID


@router.post("/{achievement_id}/grant", summary="Grant achievement to user")
async def grant_achievement(
    achievement_id: UUID,
    payload: GrantRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    granted = await AchievementsService.grant_manual(db, payload.user_id, achievement_id)
    return {"granted": granted}


@router.post("/{achievement_id}/revoke", summary="Revoke achievement from user")
async def revoke_achievement(
    achievement_id: UUID,
    payload: RevokeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    revoked = await AchievementsService.revoke_manual(db, payload.user_id, achievement_id)
    return {"revoked": revoked}
