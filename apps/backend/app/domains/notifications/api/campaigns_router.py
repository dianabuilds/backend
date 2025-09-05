from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.domains.notifications.application.broadcast_service import (
    cancel_campaign,
    estimate_recipients,
    start_campaign_async,
)
from app.domains.notifications.infrastructure.models.campaign_models import (
    CampaignStatus,
    NotificationCampaign,
)
from app.domains.users.infrastructure.models.user import User
from app.providers.db.session import get_db
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

admin_only = require_admin_role({"admin"})

router = APIRouter(
    prefix="/admin/notifications/campaigns",
    tags=["admin"],
    dependencies=[Depends(admin_only)],
    responses=ADMIN_AUTH_RESPONSES,
)


class CampaignFilters(BaseModel):
    role: str | None = None
    is_active: bool | None = None
    is_premium: bool | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None


class CampaignCreate(BaseModel):
    title: str
    message: str
    type: str = "system"
    filters: CampaignFilters | None = None


class CampaignUpdate(BaseModel):
    title: str
    message: str


@router.post("/estimate", summary="Estimate campaign recipients")
async def estimate_campaign(
    filters: CampaignFilters,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    filters_dict: dict[str, Any] = filters.model_dump()
    total = await estimate_recipients(db, filters_dict)
    return {"total": total}


@router.post("", summary="Create campaign")
async def create_campaign(
    payload: CampaignCreate,
    current_user: Annotated[User, Depends(admin_only)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    filters_dict: dict[str, Any] = payload.filters.model_dump() if payload.filters else {}
    camp = NotificationCampaign(
        title=payload.title,
        message=payload.message,
        type=payload.type,
        filters=filters_dict or None,
        status=CampaignStatus.draft,
        created_by=current_user.id,
    )
    db.add(camp)
    await db.commit()
    await db.refresh(camp)
    return {"id": str(camp.id), "status": camp.status}


@router.get("", summary="List campaigns")
async def list_campaigns(
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    stmt = (
        select(NotificationCampaign).order_by(NotificationCampaign.created_at.desc()).limit(limit)
    )
    result = await db.execute(stmt)
    items = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "title": c.title,
            "status": c.status,
            "total": c.total,
            "sent": c.sent,
            "failed": c.failed,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "started_at": c.started_at.isoformat() if c.started_at else None,
            "finished_at": c.finished_at.isoformat() if c.finished_at else None,
            "type": c.type,
        }
        for c in items
    ]


@router.get("/{campaign_id}", summary="Get campaign")
async def get_campaign(campaign_id: UUID, db: Annotated[AsyncSession, Depends(get_db)] = ...):
    camp = await db.get(NotificationCampaign, campaign_id)
    if not camp:
        raise HTTPException(status_code=404, detail="Not found")
    return {
        "id": str(camp.id),
        "title": camp.title,
        "message": camp.message,
        "status": camp.status,
        "total": camp.total,
        "sent": camp.sent,
        "failed": camp.failed,
        "created_at": camp.created_at.isoformat() if camp.created_at else None,
        "started_at": camp.started_at.isoformat() if camp.started_at else None,
        "finished_at": camp.finished_at.isoformat() if camp.finished_at else None,
        "type": camp.type,
        "filters": camp.filters or {},
    }


@router.patch("/{campaign_id}", summary="Update campaign")
async def update_campaign(
    campaign_id: UUID,
    payload: CampaignUpdate,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    current_user: Annotated[User, Depends(admin_only)] = ...,
):
    camp = await db.get(NotificationCampaign, campaign_id)
    if not camp:
        raise HTTPException(status_code=404, detail="Not found")
    camp.title = payload.title
    camp.message = payload.message
    await db.commit()
    return {"id": str(camp.id), "status": camp.status}


@router.delete("/{campaign_id}", summary="Delete campaign")
async def delete_campaign(
    campaign_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    camp = await db.get(NotificationCampaign, campaign_id)
    if not camp:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(camp)
    await db.commit()
    return {"ok": True}


@router.post("/{campaign_id}/start", summary="Start campaign")
async def start_campaign(
    campaign_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    camp = await db.get(NotificationCampaign, campaign_id)
    if not camp:
        raise HTTPException(status_code=404, detail="Not found")
    if camp.status != CampaignStatus.draft:
        raise HTTPException(status_code=400, detail="Campaign already started")
    camp.status = CampaignStatus.queued  # type: ignore[assignment]
    await db.commit()
    start_campaign_async(camp.id)
    return {"id": str(camp.id), "status": camp.status}


@router.post("/{campaign_id}/cancel", summary="Cancel campaign")
async def cancel_campaign_endpoint(
    campaign_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    ok = await cancel_campaign(db, campaign_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Not found")
    return {"ok": True}
