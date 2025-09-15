from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from apps.backendDDD.domains.platform.notifications.ports_notify import (
    INotificationRepository,
)


class NotificationRepository(INotificationRepository):
    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            create_async_engine(str(engine)) if isinstance(engine, str) else engine
        )

    async def create_and_commit(
        self,
        *,
        user_id: str,
        title: str,
        message: str,
        type_: str,
        placement: str,
        is_preview: bool = False,
    ) -> dict[str, Any]:
        sql = text(
            """
            INSERT INTO notifications(
              user_id, title, message, type, placement, is_preview, created_at
            ) VALUES (
              :user_id, :title, :message, :type, :placement, :is_preview, now()
            ) RETURNING *
            """
        )
        payload = {
            "user_id": user_id,
            "title": title,
            "message": message,
            "type": type_,
            "placement": placement,
            "is_preview": bool(is_preview),
        }
        async with self._engine.begin() as conn:
            r = (await conn.execute(sql, payload)).mappings().first()
            assert r is not None
            return dict(r)

    async def list_for_user(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        sql = text(
            "SELECT * FROM notifications WHERE user_id=:uid ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        )
        async with self._engine.begin() as conn:
            rows = (
                (
                    await conn.execute(
                        sql,
                        {"uid": user_id, "limit": int(limit), "offset": int(offset)},
                    )
                )
                .mappings()
                .all()
            )
            return [dict(r) for r in rows]

    async def mark_read(self, user_id: str, notif_id: str) -> bool:
        sql = text(
            "UPDATE notifications SET read_at = now() WHERE id = :id AND user_id = :uid AND read_at IS NULL"
        )
        async with self._engine.begin() as conn:
            res = await conn.execute(sql, {"id": notif_id, "uid": user_id})
            return res.rowcount > 0  # type: ignore[attr-defined]
