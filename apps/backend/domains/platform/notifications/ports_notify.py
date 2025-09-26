from __future__ import annotations

from collections.abc import Mapping
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
        topic_key: str | None = None,
        channel_key: str | None = None,
        priority: str = "normal",
        cta_label: str | None = None,
        cta_url: str | None = None,
        meta: Mapping[str, Any] | None = None,
        event_id: str | None = None,
    ) -> dict[str, Any]: ...

    async def list_for_user(
        self,
        user_id: str,
        *,
        placement: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]: ...
    async def mark_read(self, user_id: str, notif_id: str) -> dict[str, Any] | None: ...


class INotificationPusher(Protocol):
    async def send(self, user_id: str, payload: dict[str, Any]) -> None: ...


__all__ = ["INotificationRepository", "INotificationPusher"]
