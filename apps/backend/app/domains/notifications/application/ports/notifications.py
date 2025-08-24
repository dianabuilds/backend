from __future__ import annotations

from typing import Protocol
from uuid import UUID


class INotificationPort(Protocol):
    async def notify(
        self,
        trigger: str,
        user_id: UUID,
        *,
        workspace_id: UUID,
        title: str,
        message: str,
    ) -> None:  # pragma: no cover
        ...


__all__ = ["INotificationPort"]
