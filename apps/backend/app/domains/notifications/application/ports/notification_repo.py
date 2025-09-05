from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID


class INotificationRepository(Protocol):
    async def create_and_commit(
        self,
        *,
        workspace_id: UUID | None = None,
        user_id: UUID,
        title: str,
        message: str,
        type: Any,
        is_preview: bool = False,
    ) -> dict[str, Any]:  # pragma: no cover - контракт
        ...
