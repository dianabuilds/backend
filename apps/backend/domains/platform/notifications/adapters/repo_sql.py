from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.platform.notifications.models.entities import PreferenceRecord
from domains.platform.notifications.ports import NotificationPreferenceRepo

from ._engine import ensure_async_engine


class SQLNotificationPreferenceRepo(NotificationPreferenceRepo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = ensure_async_engine(engine)

    @staticmethod
    def _normalize_user_id(user_id: str) -> str | None:
        try:
            return str(UUID(str(user_id)))
        except (TypeError, ValueError):
            return None

    async def list_for_user(self, user_id: str) -> list[PreferenceRecord]:
        normalized = self._normalize_user_id(user_id)
        if normalized is None:
            return []
        query = text(
            """
            SELECT
                topic_key,
                channel,
                opt_in,
                digest,
                quiet_hours,
                consent_source,
                consent_version,
                updated_by,
                request_id,
                created_at,
                updated_at
            FROM notification_preferences
            WHERE user_id = cast(:uid as uuid)
            ORDER BY topic_key, channel
            """
        )
        async with self._engine.begin() as conn:
            rows = (await conn.execute(query, {"uid": normalized})).mappings().all()
        records: list[PreferenceRecord] = []
        for row in rows:
            quiet_hours_raw = row.get("quiet_hours") or []
            quiet_hours: tuple[int, ...]
            if isinstance(quiet_hours_raw, (list, tuple)):
                quiet_hours = tuple(int(v) for v in quiet_hours_raw)
            else:
                quiet_hours = tuple()
            records.append(
                PreferenceRecord(
                    user_id=normalized,
                    topic_key=str(row["topic_key"]),
                    channel_key=str(row["channel"]),
                    opt_in=bool(row["opt_in"]),
                    digest=str(row["digest"]),
                    quiet_hours=quiet_hours,
                    consent_source=str(row.get("consent_source") or "user"),
                    consent_version=int(row.get("consent_version") or 1),
                    updated_by=(str(row.get("updated_by")) if row.get("updated_by") else None),
                    request_id=(str(row.get("request_id")) if row.get("request_id") else None),
                    created_at=row.get("created_at"),
                    updated_at=row.get("updated_at"),
                )
            )
        return records

    async def replace_for_user(self, user_id: str, records: Sequence[PreferenceRecord]) -> None:
        normalized = self._normalize_user_id(user_id)
        if normalized is None:
            return
        async with self._engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM notification_preferences WHERE user_id = cast(:uid as uuid)"),
                {"uid": normalized},
            )
            if not records:
                return
            payloads: list[dict[str, Any]] = []
            for record in records:
                payloads.append(
                    {
                        "user_id": normalized,
                        "topic_key": record.topic_key,
                        "channel": record.channel_key,
                        "opt_in": bool(record.opt_in),
                        "digest": str(record.digest),
                        "quiet_hours": json.dumps(list(record.quiet_hours or ())),
                        "consent_source": record.consent_source,
                        "consent_version": int(record.consent_version),
                        "updated_by": record.updated_by,
                        "request_id": record.request_id,
                    }
                )
            await conn.execute(
                text(
                    """
                    INSERT INTO notification_preferences (
                        user_id,
                        topic_key,
                        channel,
                        opt_in,
                        digest,
                        quiet_hours,
                        consent_source,
                        consent_version,
                        updated_by,
                        request_id,
                        created_at,
                        updated_at
                    ) VALUES (
                        cast(:user_id as uuid),
                        :topic_key,
                        :channel,
                        :opt_in,
                        :digest,
                        cast(:quiet_hours as jsonb),
                        :consent_source,
                        :consent_version,
                        :updated_by,
                        :request_id,
                        now(),
                        now()
                    )
                    """
                ),
                payloads,
            )


__all__ = ["SQLNotificationPreferenceRepo"]
