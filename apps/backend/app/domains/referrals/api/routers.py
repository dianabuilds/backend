# ruff: noqa: B008, E501
from __future__ import annotations

import csv
from datetime import datetime
from io import StringIO
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.domains.admin.application.feature_flag_service import (
    FeatureFlagKey,
    get_effective_flags,
)
from app.domains.referrals.application.referrals_service import ReferralsService
from app.domains.referrals.infrastructure.repositories.referrals_repository import (
    ReferralsRepository,
)
from app.domains.users.infrastructure.models.user import User
from app.providers.db.session import get_db
from app.schemas.referrals_admin import (
    ActivateCodeOut,
    DeactivateCodeOut,
    ReferralCodeAdminOut,
    ReferralEventAdminOut,
)
from app.schemas.referrals_user import MyReferralCodeOut, MyReferralStatsOut
from app.security import ADMIN_AUTH_RESPONSES, auth_user, require_admin_role

router = APIRouter()

admin_router = APIRouter(
    prefix="/admin/referrals",
    tags=["admin", "referrals"],
    responses=ADMIN_AUTH_RESPONSES,
)
user_router = APIRouter(prefix="/referrals", tags=["referrals"])
admin_required = require_admin_role()


def _svc(db: AsyncSession) -> ReferralsService:
    return ReferralsService(ReferralsRepository(db))


class ReasonIn(BaseModel):
    reason: str | None = None


@user_router.get("/me/code", response_model=MyReferralCodeOut, summary="Get my referral code")
async def get_my_code(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
) -> MyReferralCodeOut:
    preview_header = request.headers.get("X-Feature-Flags")
    flags = await get_effective_flags(db, preview_header, current_user)
    if FeatureFlagKey.REFERRALS_PROGRAM.value not in flags:
        raise HTTPException(status_code=404, detail="Not found")
    code = await _svc(db).get_or_create_personal_code(db, current_user.id)
    return MyReferralCodeOut(code=code.code, active=bool(code.active))


@user_router.get("/me/stats", response_model=MyReferralStatsOut, summary="My referral stats")
async def get_my_stats(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
) -> MyReferralStatsOut:
    preview_header = request.headers.get("X-Feature-Flags")
    flags = await get_effective_flags(db, preview_header, current_user)
    if FeatureFlagKey.REFERRALS_PROGRAM.value not in flags:
        raise HTTPException(status_code=404, detail="Not found")
    total = await ReferralsRepository(db).count_signups(current_user.id)
    return MyReferralStatsOut(total_signups=total)


class CodesQuery(BaseModel):
    owner_user_id: UUID | None = None
    active: bool | None = None
    limit: int = 50
    offset: int = 0


@admin_router.get("/codes", response_model=list[ReferralCodeAdminOut], summary="List referral codes")
async def list_codes_admin(
    owner_user_id: UUID | None = Query(default=None),
    active: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    __: Annotated[object, Depends(admin_required)] = ...,
):
    items = await ReferralsRepository(db).list_codes(
        owner_user_id=owner_user_id,
        active=active,
        limit=limit,
        offset=offset,
    )
    return [ReferralCodeAdminOut.model_validate(it) for it in items]


@admin_router.post("/codes/{owner_user_id}/activate", response_model=ActivateCodeOut, summary="Activate personal code")
async def activate_code_admin(
    owner_user_id: UUID,
    body: ReasonIn | None = None,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    current: Annotated[User, Depends(auth_user)] = ...,
    __: Annotated[object, Depends(admin_required)] = ...,
):
    repo = ReferralsRepository(db)
    code = await repo.set_active(owner_user_id, True)
    if not code:
        raise HTTPException(status_code=404, detail="Code not found")
    # audit
    try:
        from app.domains.audit.application.audit_service import audit_log
        await audit_log(db, actor_id=str(current.id), action="referral_code_activate", resource_type="referral_code",
                        resource_id=str(code.id),
                        after={"active": True, "code": code.code, "owner_user_id": str(owner_user_id)},
                        reason=(body.reason if body else None))
    except Exception:
        pass
    return ActivateCodeOut(code=code.code)


@admin_router.post("/codes/{owner_user_id}/deactivate", response_model=DeactivateCodeOut, summary="Deactivate personal code")
async def deactivate_code_admin(
    owner_user_id: UUID,
    body: ReasonIn | None = None,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    current: Annotated[User, Depends(auth_user)] = ...,
    __: Annotated[object, Depends(admin_required)] = ...,
):
    repo = ReferralsRepository(db)
    code = await repo.set_active(owner_user_id, False)
    if not code:
        raise HTTPException(status_code=404, detail="Code not found")
    # audit
    try:
        from app.domains.audit.application.audit_service import audit_log
        await audit_log(db, actor_id=str(current.id), action="referral_code_deactivate", resource_type="referral_code",
                        resource_id=str(code.id),
                        after={"active": False, "code": code.code, "owner_user_id": str(owner_user_id)},
                        reason=(body.reason if body else None))
    except Exception:
        pass
    return DeactivateCodeOut()


@admin_router.get("/events", response_model=list[ReferralEventAdminOut], summary="List referral events")
async def list_events_admin(
    referrer_user_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    __: Annotated[object, Depends(admin_required)] = ...,
):
    repo = ReferralsRepository(db)
    items0 = await repo.list_events(
        referrer_user_id=referrer_user_id,
        limit=limit,
        offset=offset,
    )
    if date_from or date_to:
        items = []
        for it in items0:
            if date_from and it.occurred_at < date_from:
                continue
            if date_to and it.occurred_at > date_to:
                continue
            items.append(it)
    else:
        items = items0
    return [ReferralEventAdminOut.model_validate(it) for it in items]


@admin_router.get("/events/export", summary="Export referral events as CSV")
async def export_events_admin(
    referrer_user_id: UUID | None = Query(default=None),
    limit: int = Query(default=10000, ge=1, le=100000),
    offset: int = Query(default=0, ge=0),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    __: Annotated[object, Depends(admin_required)] = ...,
):
    repo = ReferralsRepository(db)
    items0 = await repo.list_events(referrer_user_id=referrer_user_id, limit=limit, offset=offset)
    if date_from or date_to:
        items = []
        for it in items0:
            if date_from and it.occurred_at < date_from:
                continue
            if date_to and it.occurred_at > date_to:
                continue
            items.append(it)
    else:
        items = items0

    def _stream() -> str:
        buf = StringIO()
        writer = csv.writer(buf)
        writer.writerow(["id", "code", "referrer_user_id", "referee_user_id", "event_type", "occurred_at"])
        for it in items:
            writer.writerow([
                str(it.id),
                it.code or "",
                str(it.referrer_user_id) if it.referrer_user_id else "",
                str(it.referee_user_id),
                it.event_type,
                it.occurred_at.isoformat(),
            ])
        buf.seek(0)
        return buf.getvalue()

    return StreamingResponse(iter([_stream()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=referral_events.csv"})


router.include_router(user_router)
router.include_router(admin_router)
