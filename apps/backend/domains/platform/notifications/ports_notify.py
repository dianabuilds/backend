from __future__ import annotations

from typing import Any, Protocol


class INotificationRepository(Protocol):
    async def create_and_commit(
        self,
        *,
        user_id: str,
        title: str,
        message: str,
        type_: str,
        placement: str,
        is_preview: bool = False,
    ) -> dict[str, Any]: ...

    async def list_for_user(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]: ...
    async def mark_read(self, user_id: str, notif_id: str) -> bool: ...


class INotificationPusher(Protocol):
    async def send(self, user_id: str, payload: dict[str, Any]) -> None: ...


__all__ = ["INotificationRepository", "INotificationPusher"]
