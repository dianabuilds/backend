from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Mapping
from collections.abc import Mapping as TypingMapping
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)

_TABLE = "platform_moderation_state"
_ROW_KEY = "singleton"

__all__ = ["SQLModerationStorage"]


class SQLModerationStorage:
    """Persist platform moderation state in Postgres."""

    def __init__(self, engine: AsyncEngine | None) -> None:
        self._engine = engine
        self._lock = asyncio.Lock()
        self._ready = False

    def enabled(self) -> bool:
        return self._engine is not None

    async def load(self) -> dict[str, Any]:
        if self._engine is None:
            return {}
        async with self._lock:
            await self._ensure_table()
            async with self._engine.begin() as conn:
                row = (
                    (
                        await conn.execute(
                            text(f"SELECT payload FROM {_TABLE} WHERE id = :id"),
                            {"id": _ROW_KEY},
                        )
                    )
                    .mappings()
                    .first()
                )
            if not row:
                return {}
            try:
                raw = json.loads(row["payload"])
            except (json.JSONDecodeError, TypeError) as exc:
                logger.warning("Failed to decode moderation snapshot: %s", exc)
                return {}
            if isinstance(raw, TypingMapping):
                return dict(raw)
            logger.warning("Unexpected moderation snapshot payload type: %s", type(raw))
            return {}

    async def save(self, payload: Mapping[str, Any]) -> None:
        if self._engine is None:
            return
        blob = json.dumps(payload, ensure_ascii=False)
        async with self._lock:
            await self._ensure_table()
            async with self._engine.begin() as conn:
                await conn.execute(
                    text(
                        f"""
                        INSERT INTO {_TABLE} (id, payload)
                        VALUES (:id, :payload)
                        ON CONFLICT (id) DO UPDATE SET
                            payload = EXCLUDED.payload,
                            updated_at = now()
                        """
                    ),
                    {"id": _ROW_KEY, "payload": blob},
                )

    async def _ensure_table(self) -> None:
        if self._engine is None or self._ready:
            return
        async with self._engine.begin() as conn:
            await conn.execute(
                text(
                    f"""
                    CREATE TABLE IF NOT EXISTS {_TABLE} (
                        id text PRIMARY KEY,
                        payload jsonb NOT NULL,
                        updated_at timestamptz NOT NULL DEFAULT now()
                    )
                    """
                )
            )
        self._ready = True
