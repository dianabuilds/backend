from __future__ import annotations

import logging
from asyncio import TimeoutError as AsyncTimeoutError
from typing import Any

from domains.platform.notifications.application.interactors.commands import (
    NotificationCreateCommand,
)
from domains.platform.notifications.application.interactors.push import (
    NotificationPushInteractor,
    NotificationPushRequest,
)
from domains.platform.notifications.ports_notify import (
    INotificationPusher,
    INotificationRepository,
)
from packages.core import with_trace

logger = logging.getLogger(__name__)

_PUSH_RETRY_EXCEPTIONS = (
    RuntimeError,
    ConnectionError,
    OSError,
    AsyncTimeoutError,
    ValueError,
)


class NotifyService:
    def __init__(
        self,
        repo: INotificationRepository,
        pusher: INotificationPusher,
        *,
        push_interactor: NotificationPushInteractor | None = None,
    ) -> None:
        self._repo = repo
        self._push = push_interactor or NotificationPushInteractor(
            pusher, retry_exceptions=_PUSH_RETRY_EXCEPTIONS
        )

    @with_trace
    async def create_notification(
        self, command: NotificationCreateCommand
    ) -> dict[str, Any]:
        payload = command.to_repo_payload()
        dto = await self._repo.create_and_commit(**payload)
        if not command.is_preview:
            await self._push.send(
                NotificationPushRequest(user_id=command.user_id, payload=dto)
            )
        return dto


__all__ = ["NotifyService"]
