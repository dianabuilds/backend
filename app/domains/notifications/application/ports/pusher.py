from __future__ import annotations

from typing import Any, Dict, Protocol
from uuid import UUID


class INotificationPusher(Protocol):
    async def send(self, user_id: UUID, data: Dict[str, Any]) -> None:  # pragma: no cover - контракт
        ...
