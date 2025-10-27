from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from .._engine import ensure_async_engine


class NotificationConfigRepository:
    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine = ensure_async_engine(engine)

    async def get_retention(self) -> dict[str, Any] | None:
        sql = text(
            """
            SELECT
                value,
                updated_at,
                updated_by::text AS updated_by
            FROM notification_config
            WHERE key = :key
            """
        )
        async with self._engine.begin() as conn:
            row = (await conn.execute(sql, {"key": "retention"})).mappings().first()
        if row is None:
            return None
        return self._normalize_retention_row(row)

    async def upsert_retention(
        self,
        *,
        retention_days: int | None,
        max_per_user: int | None,
        actor_id: str | None,
    ) -> dict[str, Any]:
        payload = {
            "retention_days": retention_days,
            "max_per_user": max_per_user,
        }
        sql = text(
            """
            INSERT INTO notification_config (key, value, updated_at, updated_by)
            VALUES (:key, CAST(:value AS jsonb), now(), CAST(:updated_by AS uuid))
            ON CONFLICT (key) DO UPDATE SET
                value = EXCLUDED.value,
                updated_at = now(),
                updated_by = EXCLUDED.updated_by
            RETURNING
                value,
                updated_at,
                updated_by::text AS updated_by
            """
        )
        params = {
            "key": "retention",
            "value": json.dumps(payload, ensure_ascii=False),
            "updated_by": actor_id,
        }
        async with self._engine.begin() as conn:
            row = (await conn.execute(sql, params)).mappings().first()
        if row is None:
            return {
                "retention_days": retention_days,
                "max_per_user": max_per_user,
                "updated_at": None,
                "updated_by": actor_id,
            }
        return self._normalize_retention_row(row)

    @staticmethod
    def _coerce_int(value: Any) -> int | None:
        if value is None:
            return None
        try:
            number = int(value)
        except (TypeError, ValueError):
            return None
        return number

    def _normalize_retention_row(self, row: Mapping[str, Any]) -> dict[str, Any]:
        raw_value = row.get("value")
        if isinstance(raw_value, str):
            try:
                parsed: Mapping[str, Any] | None = json.loads(raw_value)
            except json.JSONDecodeError:
                parsed = None
        elif isinstance(raw_value, Mapping):
            parsed = raw_value
        else:
            parsed = None
        payload = dict(parsed or {})
        retention_days = self._coerce_int(payload.get("retention_days"))
        max_per_user = self._coerce_int(payload.get("max_per_user"))
        updated_at_raw = row.get("updated_at")
        updated_by = row.get("updated_by")
        if updated_at_raw is not None and hasattr(updated_at_raw, "isoformat"):
            updated_at = updated_at_raw.isoformat()
        else:
            updated_at = None
        return {
            "retention_days": retention_days,
            "max_per_user": max_per_user,
            "updated_at": updated_at,
            "updated_by": str(updated_by) if updated_by else None,
        }


__all__ = ["NotificationConfigRepository"]
