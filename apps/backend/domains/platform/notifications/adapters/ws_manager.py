from __future__ import annotations

import asyncio

from fastapi import WebSocket


class WebSocketManager:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._clients: dict[str, set[WebSocket]] = {}

    async def connect(self, user_id: str, ws: WebSocket) -> None:
        async with self._lock:
            self._clients.setdefault(user_id, set()).add(ws)

    async def disconnect(self, user_id: str, ws: WebSocket) -> None:
        async with self._lock:
            try:
                self._clients.get(user_id, set()).discard(ws)
                if not self._clients.get(user_id):
                    self._clients.pop(user_id, None)
            except Exception:
                pass

    async def send(self, user_id: str, payload: dict) -> None:
        conns = list(self._clients.get(user_id, set()))
        for ws in conns:
            try:
                await ws.send_json(payload)
            except Exception:
                # Remove broken connection
                await self.disconnect(user_id, ws)


__all__ = ["WebSocketManager"]
