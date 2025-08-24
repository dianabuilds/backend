from __future__ import annotations

from typing import Any, Dict, Protocol
from uuid import UUID


class INotificationRepository(Protocol):
    async def create_and_commit(
        self,
        *,
        workspace_id: UUID,
        user_id: UUID,
        title: str,
        message: str,
        type: Any,
    ) -> Dict[str, Any]:  # pragma: no cover - контракт
        ...
