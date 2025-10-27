from __future__ import annotations

import asyncio
import logging

from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._clients: dict[str, set[WebSocket]] = {}

    async def connect(self, user_id: str, ws: WebSocket) -> None:
        async with self._lock:
            self._clients.setdefault(user_id, set()).add(ws)

    async def disconnect(self, user_id: str, ws: WebSocket) -> None:
        async with self._lock:
            bucket = self._clients.get(user_id)
            if bucket is None:
                return
            bucket.discard(ws)
            if not bucket:
                self._clients.pop(user_id, None)

    async def send(self, user_id: str, payload: dict) -> None:
        conns = list(self._clients.get(user_id, set()))
        if not conns:
            logger.debug("notifications.ws.no_clients", extra={"user_id": user_id})
            return
        for ws in conns:
            try:
                await ws.send_json(payload)
            except (WebSocketDisconnect, RuntimeError, ConnectionError) as exc:
                logger.debug(
                    "notifications.ws.send_failed",
                    extra={"user_id": user_id},
                    exc_info=exc,
                )
                await self.disconnect(user_id, ws)


__all__ = ["WebSocketManager"]
