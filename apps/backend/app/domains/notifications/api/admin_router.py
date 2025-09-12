from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.notifications.application.notify_service import NotifyService
from app.domains.notifications.infrastructure.repositories import (
    notification_repository as notification_repo,
)
from app.domains.notifications.infrastructure.transports.websocket import (
    WebsocketPusher,
)
from app.domains.notifications.infrastructure.transports.websocket import (
    manager as ws_manager,
)
from app.domains.users.infrastructure.models.user import User
from app.kernel.db import get_db
from app.schemas.notification import NotificationCreate
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

admin_required = require_admin_role({"admin"})

router = APIRouter(
    prefix="/admin/notifications",
    tags=["admin"],
    dependencies=[Depends(admin_required)],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.post("", summary="Send notification to user")
async def send_notification(
    payload: NotificationCreate,
    current_user: Annotated[User, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    user = await db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    svc = NotifyService(
        notification_repo.NotificationRepository(db),
        WebsocketPusher(ws_manager),
    )
    notif = await svc.create_notification(
        user_id=payload.user_id,
        title=payload.title,
        message=payload.message,
        type=payload.type,
        placement=payload.placement,
    )
    try:
        notif_id = str(notif.get("id"))  # repository returns dict
    except Exception:
        notif_id = ""
    return {"id": notif_id, "status": "queued"}

