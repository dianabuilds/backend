from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from domains.platform.notifications.ports_notify import (
    INotificationRepository,
)


class NotificationRepository(INotificationRepository):
    def __init__(self, engine: AsyncEngine | str) -> None:
        if isinstance(engine, str):
            dsn = str(engine)
            try:
                from urllib.parse import parse_qsl, urlparse, urlunparse

                u = urlparse(dsn)
                scheme = u.scheme
                if scheme.startswith("postgresql") and not scheme.startswith("postgresql+asyncpg"):
                    scheme = "postgresql+asyncpg"
                raw_pairs = parse_qsl(u.query)
                ssl_flag = None
                for key, value in raw_pairs:
                    lower_key = key.lower()
                    if lower_key == "ssl":
                        ssl_flag = str(value).lower() in {"1", "true", "yes"}
                        continue
                    if lower_key == "sslmode":
                        sm = str(value).lower()
                        if sm in {"require", "verify-full", "verify-ca"}:
                            ssl_flag = True
                        elif sm in {"disable", "allow", "prefer", "0", "false"}:
                            ssl_flag = False
                        continue
                dsn_no_query = urlunparse((scheme, u.netloc, u.path, u.params, "", u.fragment))
            except Exception:
                ssl_flag = None
                dsn_no_query = dsn
            kwargs = {"connect_args": {}}  # type: ignore[var-annotated]
            if ssl_flag is not None:
                kwargs["connect_args"] = {"ssl": ssl_flag}
            self._engine = create_async_engine(dsn_no_query, **kwargs)
        else:
            self._engine = engine

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
