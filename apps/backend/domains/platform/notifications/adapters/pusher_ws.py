from __future__ import annotations

from typing import Any

from domains.platform.notifications.adapters.ws_manager import (
    WebSocketManager,
)
from domains.platform.notifications.ports_notify import (
    INotificationPusher,
)


class WebSocketPusher(INotificationPusher):
    def __init__(self, manager: WebSocketManager) -> None:
        self._manager = manager

    async def send(self, user_id: str, payload: dict[str, Any]) -> None:
        await self._manager.send(user_id, payload)


__all__ = ["WebSocketPusher"]
