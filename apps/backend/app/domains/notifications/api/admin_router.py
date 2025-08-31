from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.domains.notifications.application.notify_service import NotifyService
from app.domains.notifications.infrastructure.models.notification_models import (
    NotificationType,
)
from app.domains.notifications.infrastructure.repositories.notification_repository import (
    NotificationRepository,
)
from app.domains.notifications.infrastructure.transports.websocket import (
    WebsocketPusher,
)
from app.domains.notifications.infrastructure.transports.websocket import (
    manager as ws_manager,
)
from app.domains.users.infrastructure.models.user import User
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

admin_required = require_admin_role({"admin"})

router = APIRouter(
    prefix="/admin/notifications",
    tags=["admin"],
    dependencies=[Depends(admin_required)],
    responses=ADMIN_AUTH_RESPONSES,
)


class SendNotificationPayload(BaseModel):
    workspace_id: UUID
    user_id: UUID
    title: str
    message: str
    type: NotificationType = NotificationType.system


@router.post("", summary="Send notification to user")
async def send_notification(
    payload: SendNotificationPayload,
    current_user: Annotated[User, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    user = await db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    svc = NotifyService(NotificationRepository(db), WebsocketPusher(ws_manager))
    notif = await svc.create_notification(
        workspace_id=payload.workspace_id,
        user_id=payload.user_id,
        title=payload.title,
        message=payload.message,
        type=payload.type,
    )
    return {"id": str(notif.id), "status": "queued"}
