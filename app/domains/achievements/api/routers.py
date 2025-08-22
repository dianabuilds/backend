from __future__ import annotations
from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domains.achievements.application.admin_service import AchievementsAdminService
from app.domains.achievements.application.achievements_service import AchievementsService
from app.domains.achievements.infrastructure.repositories.achievements_repository import AchievementsRepository
from app.domains.achievements.infrastructure.notifications_adapter import NotificationsAdapter
from app.domains.users.infrastructure.models.user import User
from app.schemas.achievement_admin import (
    AchievementAdminOut,
    AchievementCreateIn,
    AchievementUpdateIn,
)
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(prefix="/admin/achievements", tags=["admin", "achievements"], responses=ADMIN_AUTH_RESPONSES)
admin_required = require_admin_role()


def _admin_svc(db: AsyncSession) -> AchievementsAdminService:
    return AchievementsAdminService(AchievementsRepository(db))


def _svc(db: AsyncSession) -> AchievementsService:
    return AchievementsService(AchievementsRepository(db), NotificationsAdapter(db))


@router.get("", response_model=List[AchievementAdminOut], summary="List achievements (admin)")
async def list_achievements_admin(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_required),
) -> List[AchievementAdminOut]:
    rows = await _admin_svc(db).list()
    return [AchievementAdminOut.model_validate(r) for r in rows]


@router.post("", response_model=AchievementAdminOut, summary="Create achievement")
async def create_achievement_admin(
    body: AchievementCreateIn,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_required),
) -> AchievementAdminOut:
    data = {
        "code": body.code.strip(),
        "title": body.title.strip(),
        "description": body.description or None,
        "icon": body.icon or None,
        "visible": bool(body.visible),
        "condition": body.condition or {},
    }
    try:
        item = await _admin_svc(db).create(db, data)
    except ValueError as e:
        if str(e) == "code_conflict":
            raise HTTPException(status_code=409, detail="Code already exists")
        raise
    return AchievementAdminOut.model_validate(item)


@router.patch("/{achievement_id}", response_model=AchievementAdminOut, summary="Update achievement")
async def update_achievement_admin(
    achievement_id: UUID,
    body: AchievementUpdateIn,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_required),
) -> AchievementAdminOut:
    data = body.model_dump(exclude_unset=True)
    try:
        item = await _admin_svc(db).update(db, achievement_id, data)
    except ValueError as e:
        if str(e) == "code_conflict":
            raise HTTPException(status_code=409, detail="Code already exists")
        raise
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return AchievementAdminOut.model_validate(item)


@router.delete("/{achievement_id}", summary="Delete achievement")
async def delete_achievement_admin(
    achievement_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_required),
):
    ok = await _admin_svc(db).delete(db, achievement_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Not found")
    return {"ok": True}


@router.post("/{achievement_id}/grant", summary="Grant achievement to user")
async def grant_achievement(
    achievement_id: UUID,
    payload: AchievementCreateIn.__class__(code="").model_rebuild(),  # placeholder type, not used
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    # ожидаем тело {"user_id": "..."}
    from pydantic import BaseModel

    class GrantRequest(BaseModel):
        user_id: UUID

    req = GrantRequest.model_validate(payload)
    granted = await _svc(db).grant_manual(db, req.user_id, achievement_id)
    return {"granted": granted}


@router.post("/{achievement_id}/revoke", summary="Revoke achievement from user")
async def revoke_achievement(
    achievement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_required),
):
    from pydantic import BaseModel

    class RevokeRequest(BaseModel):
        user_id: UUID

    # FastAPI сам распарсит тело
    def _parse_request(req_cls):
        return req_cls  # stub

    # Этот эндпоинт примет тело {"user_id": "..."}
    # Для совместимости, определим внутри:
    return {"detail": "Use domain router grant/revoke with body {'user_id': ...}"}  # pragma: no cover
from fastapi import APIRouter

router = APIRouter()

from app.api.achievements import router as achievements_router  # noqa: E402
from app.api.admin_achievements import router as admin_achievements_router  # noqa: E402

router.include_router(achievements_router)
router.include_router(admin_achievements_router)
