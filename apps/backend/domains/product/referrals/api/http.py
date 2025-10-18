from __future__ import annotations

import csv
from datetime import datetime
from io import StringIO
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from apps.backend.app.api_gateway.routers import get_container
from domains.platform.iam.application.facade import (
    csrf_protect,
    get_current_user,
    require_admin,
)


class MyReferralCodeOut(BaseModel):
    code: str
    active: bool


class MyReferralStatsOut(BaseModel):
    total_signups: int


class ReasonIn(BaseModel):
    reason: str | None = None


class ReferralCodeAdminOut(BaseModel):
    id: UUID
    owner_user_id: UUID | None = None
    code: str
    uses_count: int
    active: bool
    created_at: datetime | None = None


class ReferralEventAdminOut(BaseModel):
    id: UUID
    code_id: UUID | None = None
    code: str | None = None
    referrer_user_id: UUID | None = None
    referee_user_id: UUID
    event_type: str
    occurred_at: datetime


class ActivateCodeOut(BaseModel):
    ok: bool = True
    code: str


class DeactivateCodeOut(BaseModel):
    ok: bool = True


def make_router() -> APIRouter:
    router = APIRouter()

    user = APIRouter(prefix="/v1/referrals", tags=["referrals"])
    admin = APIRouter(prefix="/v1/admin/referrals", tags=["admin", "referrals"])

    @user.get(
        "/me/code", response_model=MyReferralCodeOut, summary="Get my referral code"
    )
    async def get_my_code(
        claims=Depends(get_current_user), container=Depends(get_container)
    ) -> MyReferralCodeOut:
        uid = str(claims.get("sub") or "")
        if not uid:
            raise HTTPException(status_code=401, detail="unauthorized")
        code = await container.referrals_service.get_or_create_personal_code(uid)
        return MyReferralCodeOut(code=code.code, active=bool(code.active))

    @user.get(
        "/me/stats", response_model=MyReferralStatsOut, summary="My referral stats"
    )
    async def get_my_stats(
        claims=Depends(get_current_user), container=Depends(get_container)
    ) -> MyReferralStatsOut:
        uid = str(claims.get("sub") or "")
        if not uid:
            raise HTTPException(status_code=401, detail="unauthorized")
        total = await container.referrals_repo.count_signups(uid)
        return MyReferralStatsOut(total_signups=int(total))

    @admin.get(
        "/codes",
        response_model=list[ReferralCodeAdminOut],
        summary="List referral codes",
    )
    async def list_codes_admin(
        owner_user_id: UUID | None = Query(default=None),
        active: bool | None = Query(default=None),
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ):
        items = await container.referrals_repo.list_codes(
            owner_user_id=str(owner_user_id) if owner_user_id else None,
            active=active,
            limit=limit,
            offset=offset,
        )
        return [
            ReferralCodeAdminOut(
                id=UUID(it.id),
                owner_user_id=UUID(it.owner_user_id),
                code=it.code,
                uses_count=int(it.uses_count or 0),
                active=bool(it.active),
                created_at=it.created_at,
            )
            for it in items
        ]

    @admin.post(
        "/codes/{owner_user_id}/activate",
        response_model=ActivateCodeOut,
        summary="Activate personal code",
    )
    async def activate_code_admin(
        owner_user_id: UUID,
        body: ReasonIn | None = None,
        _csrf: None = Depends(csrf_protect),
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ):
        code = await container.referrals_service.set_active(str(owner_user_id), True)
        if not code:
            raise HTTPException(status_code=404, detail="not_found")
        return ActivateCodeOut(code=code.code)

    @admin.post(
        "/codes/{owner_user_id}/deactivate",
        response_model=DeactivateCodeOut,
        summary="Deactivate personal code",
    )
    async def deactivate_code_admin(
        owner_user_id: UUID,
        body: ReasonIn | None = None,
        _csrf: None = Depends(csrf_protect),
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ):
        code = await container.referrals_service.set_active(str(owner_user_id), False)
        if not code:
            raise HTTPException(status_code=404, detail="not_found")
        return DeactivateCodeOut()

    @admin.get(
        "/events",
        response_model=list[ReferralEventAdminOut],
        summary="List referral events",
    )
    async def list_events_admin(
        referrer_user_id: UUID | None = Query(default=None),
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        date_from: datetime | None = Query(default=None),
        date_to: datetime | None = Query(default=None),
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ):
        items0 = await container.referrals_repo.list_events(
            referrer_user_id=str(referrer_user_id) if referrer_user_id else None,
            limit=limit,
            offset=offset,
        )
        if date_from or date_to:
            items: list = []
            for it in items0:
                if date_from and it.occurred_at < date_from:
                    continue
                if date_to and it.occurred_at > date_to:
                    continue
                items.append(it)
        else:
            items = items0
        return [
            ReferralEventAdminOut(
                id=UUID(it.id),
                code_id=UUID(it.code_id) if it.code_id else None,
                code=it.code,
                referrer_user_id=(
                    UUID(it.referrer_user_id) if it.referrer_user_id else None
                ),
                referee_user_id=UUID(it.referee_user_id),
                event_type=it.event_type,
                occurred_at=it.occurred_at,
            )
            for it in items
        ]

    @admin.get("/events/export", summary="Export referral events as CSV")
    async def export_events_admin(
        referrer_user_id: UUID | None = Query(default=None),
        limit: int = Query(default=10000, ge=1, le=100000),
        offset: int = Query(default=0, ge=0),
        date_from: datetime | None = Query(default=None),
        date_to: datetime | None = Query(default=None),
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ):
        items0 = await container.referrals_repo.list_events(
            referrer_user_id=str(referrer_user_id) if referrer_user_id else None,
            limit=limit,
            offset=offset,
        )
        if date_from or date_to:
            items: list = []
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
            writer.writerow(
                [
                    "id",
                    "code",
                    "referrer_user_id",
                    "referee_user_id",
                    "event_type",
                    "occurred_at",
                ]
            )
            for it in items:
                writer.writerow(
                    [
                        str(it.id),
                        it.code or "",
                        str(it.referrer_user_id) if it.referrer_user_id else "",
                        str(it.referee_user_id),
                        it.event_type,
                        it.occurred_at.isoformat(),
                    ]
                )
            buf.seek(0)
            return buf.getvalue()

        return StreamingResponse(
            iter([_stream()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=referral_events.csv"},
        )

    router.include_router(user)
    router.include_router(admin)
    return router
