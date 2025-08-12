from __future__ import annotations

from pydantic import BaseModel
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role
from app.services.notifications import create_notification
from app.models.notification import NotificationType

admin_required = require_admin_role({"admin"})

router = APIRouter(
    prefix="/admin/notifications",
    tags=["admin"],
    dependencies=[Depends(admin_required)],
    responses=ADMIN_AUTH_RESPONSES,
)


class SendNotificationPayload(BaseModel):
    user_id: UUID
    title: str
    message: str
    type: NotificationType = NotificationType.system


@router.post("", summary="Send notification to user")
async def send_notification(
    payload: SendNotificationPayload,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    # Проверим, что пользователь существует
    user = await db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    notif = await create_notification(
        db=db,
        user_id=payload.user_id,
        title=payload.title,
        message=payload.message,
        type=payload.type,
    )
    return {"id": str(notif.id), "status": "queued"}
