from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import get_current_user
from app.core.security import verify_access_token
from app.db.session import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationOut
from app.services.notification_ws import manager as ws_manager

router = APIRouter(prefix="/notifications", tags=["notifications"])
ws_router = APIRouter()


@router.get("", response_model=list[NotificationOut], summary="List notifications")
async def list_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all notifications for the current user sorted by creation time."""
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
    )
    return result.scalars().all()


@router.post(
    "/{notification_id}/read",
    response_model=dict,
    summary="Mark notification read",
)
async def mark_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a specific notification as read."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notif = result.scalars().first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.read_at = datetime.utcnow()
    await db.commit()
    return {"status": "ok"}


@ws_router.websocket("/ws/notifications")
async def notifications_websocket(
    websocket: WebSocket,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """WebSocket endpoint that pushes notifications to the client."""
    user_id_str = verify_access_token(token)
    if not user_id_str:
        await websocket.close(code=1008)
        return
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        await websocket.close(code=1008)
        return
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        await websocket.close(code=1008)
        return
    await ws_manager.connect(user.id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(user.id, websocket)
