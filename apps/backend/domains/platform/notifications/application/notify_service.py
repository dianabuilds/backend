from __future__ import annotations

from typing import Any

from domains.platform.notifications.ports_notify import (
    INotificationPusher,
    INotificationRepository,
)


class NotifyService:
    def __init__(
        self, repo: INotificationRepository, pusher: INotificationPusher
    ) -> None:
        self._repo = repo
        self._pusher = pusher

    async def create_notification(
        self,
        *,
        user_id: str,
        title: str,
        message: str,
        type_: str,
        placement: str = "inbox",
        is_preview: bool = False,
    ) -> dict[str, Any]:
        dto = await self._repo.create_and_commit(
            user_id=user_id,
            title=title,
            message=message,
            type=type_,
            placement=placement,
            is_preview=is_preview,
        )
        if not is_preview:
            try:
                await self._pusher.send(user_id, dto)
            except Exception:
                pass
        return dto


__all__ = ["NotifyService"]
