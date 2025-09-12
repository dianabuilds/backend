from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.kernel.preview import PreviewContext


class INotificationPort(Protocol):
    async def notify(
        self,
        trigger: str,
        user_id: UUID,
        *,
        title: str,
        message: str,
        preview: PreviewContext | None = None,
    ) -> None:  # pragma: no cover
        ...


__all__ = ["INotificationPort"]

