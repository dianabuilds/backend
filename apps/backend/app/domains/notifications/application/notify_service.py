from __future__ import annotations

from typing import Any
from uuid import UUID

from app.core.preview import PreviewContext
from app.domains.notifications.application.ports.notification_repo import (
    INotificationRepository,
)
from app.domains.notifications.application.ports.pusher import INotificationPusher
from app.domains.workspaces.limits import workspace_limit


class NotifyService:
    def __init__(
        self, repo: INotificationRepository, pusher: INotificationPusher
    ) -> None:
        self._repo = repo
        self._pusher = pusher

    @workspace_limit("notif_per_day", scope="day", amount=1, degrade=True)
    async def create_notification(
        self,
        *,
        workspace_id: UUID,
        user_id: UUID,
        title: str,
        message: str,
        type: Any,
        preview: PreviewContext | None = None,
    ) -> dict[str, Any]:
        is_shadow = bool(preview and preview.mode == "shadow")
        dto = await self._repo.create_and_commit(
            workspace_id=workspace_id,
            user_id=user_id,
            title=title,
            message=message,
            type=type,
            is_preview=is_shadow,
        )
        if not is_shadow:
            try:
                await self._pusher.send(user_id, dto)
            except Exception:
                pass
        return dto
