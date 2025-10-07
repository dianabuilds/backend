from __future__ import annotations

import logging
from uuid import UUID

from app.api_gateway.routers import get_container
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from domains.platform.iam.security import (
    csrf_protect,
    get_current_user,
    require_admin,
)
from domains.product.achievements.api.schemas import (
    AchievementAdminOut,
    AchievementCreateIn,
    AchievementOut,
    AchievementUpdateIn,
)

logger = logging.getLogger(__name__)


def _safe_uuid(value: str | None) -> UUID | None:
    if not value:
        return None
    try:
        return UUID(str(value))
    except (ValueError, TypeError):
        logger.debug("achievements_api: invalid UUID %s", value)
        return None


class UserIdIn(BaseModel):
    user_id: UUID
    reason: str | None = None


def make_router() -> APIRouter:
    router = APIRouter()

    user = APIRouter(prefix="/v1/achievements", tags=["achievements"])
    admin = APIRouter(prefix="/v1/admin/achievements", tags=["admin", "achievements"])

    # no-op helper placeholder removed

    @admin.get(
        "",
        response_model=list[AchievementAdminOut],
        summary="List achievements (admin)",
    )
    async def list_achievements_admin(
        _: None = Depends(require_admin), container=Depends(get_container)
    ) -> list[AchievementAdminOut]:
        rows = await container.achievements_admin.list()
        return [
            AchievementAdminOut(
                id=UUID(r.id),
                code=r.code,
                title=r.title,
                description=r.description,
                icon=r.icon,
                visible=bool(r.visible),
                condition=dict(r.condition or {}),
                created_by_user_id=(_safe_uuid(r.created_by_user_id)),
                updated_by_user_id=(_safe_uuid(r.updated_by_user_id)),
            )
            for r in rows
        ]

    @admin.post("", response_model=AchievementAdminOut, summary="Create achievement")
    async def create_achievement_admin(
        body: AchievementCreateIn,
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ) -> AchievementAdminOut:
        data = {
            "code": (body.code or "").strip(),
            "title": (body.title or "").strip(),
            "description": body.description or None,
            "icon": body.icon or None,
            "visible": bool(body.visible),
            "condition": body.condition or {},
        }
        try:
            actor = str(claims.get("sub") or "")
            item = await container.achievements_admin.create(data, actor)
        except ValueError as err:
            if str(err) == "code_conflict":
                raise HTTPException(status_code=409, detail="conflict") from err
            raise
        return AchievementAdminOut(
            id=UUID(item.id),
            code=item.code,
            title=item.title,
            description=item.description,
            icon=item.icon,
            visible=bool(item.visible),
            condition=dict(item.condition or {}),
            created_by_user_id=(_safe_uuid(item.created_by_user_id)),
            updated_by_user_id=(_safe_uuid(item.updated_by_user_id)),
        )

    @admin.patch(
        "/{achievement_id}",
        response_model=AchievementAdminOut,
        summary="Update achievement",
    )
    async def update_achievement_admin(
        achievement_id: UUID,
        body: AchievementUpdateIn,
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ) -> AchievementAdminOut:
        data = body.model_dump(exclude_unset=True)
        try:
            actor = str(claims.get("sub") or "")
            item = await container.achievements_admin.update(
                str(achievement_id), data, actor
            )
        except ValueError as err:
            if str(err) == "code_conflict":
                raise HTTPException(status_code=409, detail="conflict") from err
            raise
        if not item:
            raise HTTPException(status_code=404, detail="not_found")
        return AchievementAdminOut(
            id=UUID(item.id),
            code=item.code,
            title=item.title,
            description=item.description,
            icon=item.icon,
            visible=bool(item.visible),
            condition=dict(item.condition or {}),
            created_by_user_id=(_safe_uuid(item.created_by_user_id)),
            updated_by_user_id=(_safe_uuid(item.updated_by_user_id)),
        )

    @admin.delete("/{achievement_id}", summary="Delete achievement")
    async def delete_achievement_admin(
        achievement_id: UUID,
        _csrf: None = Depends(csrf_protect),
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ):
        ok = await container.achievements_admin.delete(str(achievement_id))
        if not ok:
            raise HTTPException(status_code=404, detail="not_found")
        return {"ok": True}

    @admin.post("/{achievement_id}/grant", summary="Grant achievement to user")
    async def grant_achievement(
        achievement_id: UUID,
        body: UserIdIn,
        _csrf: None = Depends(csrf_protect),
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ):
        granted = await container.achievements_service.grant_manual(
            str(body.user_id), str(achievement_id)
        )
        return {"granted": granted}

    @admin.post("/{achievement_id}/revoke", summary="Revoke achievement from user")
    async def revoke_achievement(
        achievement_id: UUID,
        body: UserIdIn,
        _csrf: None = Depends(csrf_protect),
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ):
        revoked = await container.achievements_service.revoke_manual(
            str(body.user_id), str(achievement_id)
        )
        return {"revoked": revoked}

    @user.get("", response_model=list[AchievementOut], summary="List achievements")
    async def list_for_user(
        claims=Depends(get_current_user), container=Depends(get_container)
    ):
        uid = str(claims.get("sub") or "")
        rows = await container.achievements_service.list(uid)
        out: list[AchievementOut] = []
        for ach, ua in rows:
            out.append(
                AchievementOut(
                    id=UUID(ach.id),
                    code=ach.code,
                    title=ach.title,
                    description=ach.description,
                    icon=ach.icon,
                    unlocked=ua is not None,
                    unlocked_at=(ua.unlocked_at if ua else None),
                )
            )
        return out

    router.include_router(user)
    router.include_router(admin)
    return router
