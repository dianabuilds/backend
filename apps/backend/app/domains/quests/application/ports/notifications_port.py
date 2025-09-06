from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID


class INotificationPort(Protocol):
    async def create_notification(
        self,
        user_id: UUID,
        *,
        account_id: UUID | None = None,
        title: str,
        message: str,
        type: Any,
    ) -> None:  # pragma: no cover
        ...
