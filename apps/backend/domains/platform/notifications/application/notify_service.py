from __future__ import annotations

import logging
from asyncio import TimeoutError as AsyncTimeoutError
from collections.abc import Mapping
from typing import Any

from domains.platform.notifications.ports_notify import (
    INotificationPusher,
    INotificationRepository,
)

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
        topic_key: str | None = None,
        channel_key: str | None = None,
        priority: str = "normal",
        cta_label: str | None = None,
        cta_url: str | None = None,
        meta: Mapping[str, Any] | None = None,
        event_id: str | None = None,
    ) -> dict[str, Any]:
        dto = await self._repo.create_and_commit(
            user_id=user_id,
            title=title,
            message=message,
            type_=type_,
            placement=placement,
            is_preview=is_preview,
            topic_key=topic_key,
            channel_key=channel_key,
            priority=priority,
            cta_label=cta_label,
            cta_url=cta_url,
            meta=meta,
            event_id=event_id,
        )
        if not is_preview:
            await self._safe_push(user_id, dto)
        return dto

    async def _safe_push(self, user_id: str, payload: dict[str, Any]) -> None:
        try:
            await self._pusher.send(user_id, payload)
        except _PUSH_RETRY_EXCEPTIONS as exc:
            logger.warning(
                "notification_push_failed", extra={"user_id": user_id}, exc_info=exc
            )


__all__ = ["NotifyService"]
