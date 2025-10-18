from __future__ import annotations

import logging
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from domains.platform.notifications.ports_notify import INotificationPusher

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NotificationPushRequest:
    user_id: str
    payload: Mapping[str, Any]


class NotificationPushInteractor:
    """Encapsulates notification push logic with retry-aware logging."""

    def __init__(
        self,
        pusher: INotificationPusher,
        *,
        retry_exceptions: Sequence[type[Exception]] | None = None,
    ) -> None:
        self._pusher = pusher
        self._retry_exceptions: tuple[type[Exception], ...] = tuple(
            retry_exceptions or ()
        )

    async def send(self, request: NotificationPushRequest) -> None:
        started = time.perf_counter()
        try:
            await self._pusher.send(request.user_id, dict(request.payload))
        except self._retry_exceptions as exc:  # type: ignore[misc]
            logger.warning(
                "notification_push_retryable_failed",
                extra={"user_id": request.user_id},
                exc_info=exc,
            )
            return
        except Exception as exc:  # pragma: no cover - unexpected failure
            logger.exception(
                "notification_push_failed",
                extra={"user_id": request.user_id},
                exc_info=exc,
            )
            return
        duration_ms = (time.perf_counter() - started) * 1000
        logger.debug(
            "notification_push_sent",
            extra={"user_id": request.user_id, "duration_ms": round(duration_ms, 2)},
        )


__all__ = ["NotificationPushInteractor", "NotificationPushRequest"]
