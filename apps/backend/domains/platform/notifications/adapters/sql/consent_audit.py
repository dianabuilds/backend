from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.platform.notifications.models.entities import ConsentAuditRecord
from domains.platform.notifications.ports import NotificationConsentAuditRepo

from .._engine import ensure_async_engine


class SQLNotificationConsentAuditRepo(NotificationConsentAuditRepo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = ensure_async_engine(engine)

    @staticmethod
    def _normalize_user_id(user_id: str) -> str | None:
        try:
            return str(UUID(str(user_id)))
        except (TypeError, ValueError):
            return None

    async def append_many(self, records: Sequence[ConsentAuditRecord]) -> None:
        if not records:
            return
        payloads: list[dict[str, Any]] = []
        for record in records:
            normalized = self._normalize_user_id(record.user_id)
            if normalized is None:
                continue
            payloads.append(
                {
                    "user_id": normalized,
                    "topic_key": record.topic_key,
                    "channel": record.channel_key,
                    "previous_state": (
                        json.dumps(record.previous_state)
                        if record.previous_state is not None
                        else None
                    ),
                    "new_state": json.dumps(record.new_state),
                    "source": record.source,
                    "changed_by": record.changed_by,
                    "request_id": record.request_id,
                }
            )
        if not payloads:
            return
        async with self._engine.begin() as conn:
            await conn.execute(
                text(
                    """
                    INSERT INTO notification_consent_audit (
                        user_id,
                        topic_key,
                        channel,
                        previous_state,
                        new_state,
                        source,
                        changed_by,
                        request_id,
                        changed_at
                    ) VALUES (
                        cast(:user_id as uuid),
                        :topic_key,
                        :channel,
                        cast(:previous_state as jsonb),
                        cast(:new_state as jsonb),
                        :source,
                        :changed_by,
                        :request_id,
                        now()
                    )
                    """
                ),
                payloads,
            )


__all__ = ["SQLNotificationConsentAuditRepo"]
