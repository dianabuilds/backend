from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.models.user import User
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role
from app.services.achievements import AchievementsService

admin_required = require_admin_role()

router = APIRouter(
    prefix="/admin/achievements",
    tags=["admin", "achievements"],
    dependencies=[Depends(admin_required)],
    responses=ADMIN_AUTH_RESPONSES,
)


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
    granted = await AchievementsService.grant_manual(
    db, payload.user_id, achievement_id
    )
    return {"granted": granted}


@router.post("/{achievement_id}/revoke", summary="Revoke achievement from user")
async def revoke_achievement(
    achievement_id: UUID,
    payload: RevokeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    revoked = await AchievementsService.revoke_manual(
    db, payload.user_id, achievement_id
    )
    return {"revoked": revoked}
