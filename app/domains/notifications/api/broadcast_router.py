from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.domains.notifications.infrastructure.models.campaign_models import NotificationCampaign, CampaignStatus
from app.domains.users.infrastructure.models.user import User
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

# Доменные функции рассылки
from app.domains.notifications.application.broadcast_service import (
    estimate_recipients,
    start_campaign_async,
    cancel_campaign,
)

admin_only = require_admin_role({"admin"})

router = APIRouter(
    prefix="/admin/notifications/broadcast",
    tags=["admin"],
    dependencies=[Depends(admin_only)],
    responses=ADMIN_AUTH_RESPONSES,
)


class BroadcastFilters(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
    is_premium: Optional[bool] = None
    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None


class BroadcastCreate(BaseModel):
    title: str
    message: str
    type: str = "system"
    filters: Optional[BroadcastFilters] = None
    dry_run: bool = False


@router.post("", summary="Create broadcast campaign (or dry-run)")
async def create_broadcast(
    payload: BroadcastCreate,
    current_user: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    filters_dict: Dict[str, Any] = payload.filters.model_dump() if payload.filters else {}
    if payload.dry_run:
        total = await estimate_recipients(db, filters_dict)
        return {"dry_run": True, "total_estimate": total}

    camp = NotificationCampaign(
        title=payload.title,
        message=payload.message,
        type=payload.type,
        filters=filters_dict or None,
        status=CampaignStatus.queued,
        created_by=current_user.id,
    )
    db.add(camp)
    await db.commit()
    await db.refresh(camp)

    start_campaign_async(camp.id)
    return {"id": str(camp.id), "status": camp.status}


@router.get("", summary="List broadcast campaigns")
async def list_broadcasts(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(NotificationCampaign).order_by(NotificationCampaign.created_at.desc()).limit(limit)
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
async def get_broadcast(campaign_id: UUID, db: AsyncSession = Depends(get_db)):
    camp = await db.get(NotificationCampaign, campaign_id)
    if not camp:
        raise HTTPException(status_code=404, detail="Not found")
    return {
        "id": str(camp.id),
        "title": camp.title,
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


@router.post("/{campaign_id}/cancel", summary="Cancel campaign")
async def cancel_broadcast(campaign_id: UUID, db: AsyncSession = Depends(get_db)):
    ok = await cancel_campaign(db, campaign_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Not found")
    return {"ok": True}
