from __future__ import annotations

import logging
from typing import Any

from domains.platform.notifications.ports_notify import (
    INotificationPusher,
)


class LogPusher(INotificationPusher):
    def __init__(self) -> None:
        self._log = logging.getLogger("notifications.pusher")

    async def send(self, user_id: str, payload: dict[str, Any]) -> None:
        self._log.info("notify user %s: %s", user_id, payload)


__all__ = ["LogPusher"]
