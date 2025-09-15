from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine


class SQLOutbox:
    """Async SQL outbox publisher compatible with legacy `outbox` table.

    Usage:
        repo = SQLOutbox(engine_or_dsn)
        await repo.publish('topic.v1', payload, key='agg-id')
    """

    def __init__(self, engine: AsyncEngine | str | AsyncSession):
        if isinstance(engine, AsyncSession):
            self._session = engine
            self._engine = None
        else:
            self._session = None
            self._engine = (
                create_async_engine(str(engine)) if isinstance(engine, str) else engine
            )

    async def publish(self, topic: str, payload: dict, key: str | None = None) -> None:
        sql = text(
            """
            INSERT INTO outbox (topic, payload_json, dedup_key, status, attempts, next_retry_at)
            VALUES (:topic, cast(:payload as jsonb), :key, 'NEW', 0, now())
            """
        )
        params: dict[str, Any] = {
            "topic": topic,
            "payload": json.dumps(payload),
            "key": key,
        }
        if self._session is not None:
            await self._session.execute(sql, params)
            return
        assert self._engine is not None
        async with self._engine.begin() as conn:
            await conn.execute(sql, params)


__all__ = ["SQLOutbox"]
