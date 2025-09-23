from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from domains.platform.notifications.ports import NotificationPreferenceRepo


class SQLNotificationPreferenceRepo(NotificationPreferenceRepo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            create_async_engine(str(engine)) if isinstance(engine, str) else engine
        )

    async def get_preferences(self, user_id: str) -> dict[str, Any]:
        sql = text(
            """
            SELECT topic_key, channel, opt_in, digest, quiet_hours
            FROM notification_preferences
            WHERE user_id = cast(:uid as uuid)
            ORDER BY topic_key, channel
            """
        )
        prefs: dict[str, Any] = {}
        async with self._engine.begin() as conn:
            rows = (await conn.execute(sql, {"uid": user_id})).mappings().all()
            for row in rows:
                topic = str(row["topic_key"])
                channel = str(row["channel"])
                prefs.setdefault(topic, {})[channel] = {
                    "opt_in": bool(row["opt_in"]),
                    "digest": row.get("digest"),
                    "quiet_hours": row.get("quiet_hours") or [],
                }
        return prefs

    async def set_preferences(self, user_id: str, prefs: dict[str, Any]) -> None:
        async with self._engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM notification_preferences WHERE user_id = cast(:uid as uuid)"),
                {"uid": user_id},
            )
            rows = []
            for topic, channels in prefs.items():
                if not isinstance(channels, dict):
                    continue
                for channel, cfg in channels.items():
                    rows.append(
                        {
                            "user_id": user_id,
                            "topic_key": topic,
                            "channel": channel,
                            "opt_in": bool(cfg.get("opt_in", True)),
                            "digest": cfg.get("digest", "none"),
                            "quiet_hours": cfg.get("quiet_hours") or [],
                        }
                    )
            if rows:
                await conn.execute(
                    text(
                        """
                        INSERT INTO notification_preferences (user_id, topic_key, channel, opt_in, digest, quiet_hours, updated_at)
                        VALUES (cast(:user_id as uuid), :topic_key, :channel, :opt_in, :digest, cast(:quiet_hours as jsonb), now())
                        """
                    ),
                    rows,
                )


__all__ = ["SQLNotificationPreferenceRepo"]
