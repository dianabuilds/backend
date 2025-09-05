from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import get_current_user
from app.core.security import verify_access_token
from app.domains.notifications.infrastructure.models.notification_models import (
    Notification,
)
from app.domains.notifications.infrastructure.transports.websocket import (
    manager as ws_manager,
)
from app.domains.users.infrastructure.models.user import User
from app.providers.db.pagination import scope_by_workspace
from app.providers.db.session import get_db
from app.schemas.notification import NotificationFilter, NotificationOut

router = APIRouter(prefix="/notifications", tags=["notifications"])
ws_router = APIRouter()


@router.get("", response_model=list[NotificationOut], summary="List notifications")
async def list_notifications(
    filters: Annotated[NotificationFilter, Depends()],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    stmt = (
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .where(Notification.is_preview.is_(False))
        .order_by(Notification.created_at.desc())
    )
    if filters.workspace_id:
        stmt = scope_by_workspace(stmt, filters.workspace_id)
    if filters.placement:
        stmt = stmt.where(Notification.placement == filters.placement)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post(
    "/{notification_id}/read",
    response_model=dict,
    summary="Mark notification read",
)
async def mark_read(
    notification_id: UUID,
    filters: Annotated[NotificationFilter, Depends()],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    stmt = select(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
        Notification.is_preview.is_(False),
    )
    if filters.workspace_id:
        stmt = scope_by_workspace(stmt, filters.workspace_id)
    result = await db.execute(stmt)
    notif = result.scalars().first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.read_at = datetime.utcnow()
    await db.commit()
    return {"status": "ok"}


@ws_router.websocket("/ws/notifications")
async def notifications_websocket(
    websocket: WebSocket,
    token: Annotated[str, Query(...)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
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
