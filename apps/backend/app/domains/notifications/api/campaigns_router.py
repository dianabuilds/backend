from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.db.session import get_db
from app.domains.notifications.application.broadcast_service import start_campaign_async
from app.domains.notifications.infrastructure.models.campaign_models import (
    CampaignStatus,
    NotificationCampaign,
)
from app.domains.users.infrastructure.models.user import User
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

admin_only = require_admin_role({"admin"})

router = APIRouter(
    prefix="/admin/notifications/campaigns",
    tags=["admin"],
    dependencies=[Depends(admin_only)],
    responses=ADMIN_AUTH_RESPONSES,
)


class CampaignUpdate(BaseModel):
    title: str
    message: str


@router.get("", summary="List campaigns")
async def list_campaigns(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(NotificationCampaign)
        .order_by(NotificationCampaign.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    items = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "title": c.title,
            "message": c.message,
            "status": c.status,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in items
    ]


@router.get("/{campaign_id}", summary="Get campaign")
async def get_campaign(campaign_id: UUID, db: AsyncSession = Depends(get_db)):
    camp = await db.get(NotificationCampaign, campaign_id)
    if not camp:
        raise HTTPException(status_code=404, detail="Not found")
    return {
        "id": str(camp.id),
        "title": camp.title,
        "message": camp.message,
        "status": camp.status,
        "created_at": camp.created_at.isoformat() if camp.created_at else None,
    }


@router.patch("/{campaign_id}", summary="Update campaign")
async def update_campaign(
    campaign_id: UUID,
    payload: CampaignUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    camp = await db.get(NotificationCampaign, campaign_id)
    if not camp:
        raise HTTPException(status_code=404, detail="Not found")
    camp.title = payload.title
    camp.message = payload.message
    await db.commit()
    return {"id": str(camp.id), "status": camp.status}


@router.post("/{campaign_id}/send", summary="Dispatch campaign")
async def send_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    camp = await db.get(NotificationCampaign, campaign_id)
    if not camp:
        raise HTTPException(status_code=404, detail="Not found")
    if camp.status != CampaignStatus.draft:
        raise HTTPException(status_code=400, detail="Campaign already dispatched")
    camp.status = CampaignStatus.queued  # type: ignore[assignment]
    await db.commit()
    start_campaign_async(camp.id)
    return {"id": str(camp.id), "status": camp.status}
