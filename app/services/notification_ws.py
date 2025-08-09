from __future__ import annotations

from typing import Dict, Set
from uuid import UUID

from fastapi import WebSocket


class NotificationWSManager:
    """Manages active websocket connections for notifications."""

    def __init__(self) -> None:
        self.connections: Dict[UUID, Set[WebSocket]] = {}

    async def connect(self, user_id: UUID, websocket: WebSocket) -> None:
        """Accept connection and store it for a user."""
        await websocket.accept()
        self.connections.setdefault(user_id, set()).add(websocket)

    def disconnect(self, user_id: UUID, websocket: WebSocket) -> None:
        """Remove connection from storage."""
        conns = self.connections.get(user_id)
        if not conns:
            return
        conns.discard(websocket)
        if not conns:
            self.connections.pop(user_id, None)

    async def send_notification(self, user_id: UUID, data: dict) -> None:
        """Send JSON data to all connections of a user."""
        conns = self.connections.get(user_id)
        if not conns:
            return
        for ws in list(conns):
            try:
                await ws.send_json(data)
            except Exception:
                pass


manager = NotificationWSManager()
