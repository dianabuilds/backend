from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.platform.telemetry.ports.rum_port import IRumRepository
from packages.core.db import get_async_engine

logger = logging.getLogger(__name__)


class RumSQLRepository(IRumRepository):
    def __init__(self, engine: AsyncEngine | str) -> None:
        if isinstance(engine, AsyncEngine):
            self._engine = engine
        else:
            self._engine = get_async_engine("telemetry-rum", url=engine)

    async def add(self, event: dict[str, Any]) -> None:
        payload = dict(event or {})
        name = str(payload.get("event") or "").strip() or "unknown"
        url = str(payload.get("url") or "").strip() or "unknown"
        ts_value = payload.get("ts")
        if isinstance(ts_value, (int, float)):
            ts_ms = int(ts_value)
        else:
            ts_ms = int(datetime.now(UTC).timestamp() * 1000)
        payload["event"] = name
        payload["url"] = url
        payload["ts"] = ts_ms
        occurred_at = datetime.fromtimestamp(ts_ms / 1000.0, tz=UTC)
        sql = text(
            """
            INSERT INTO telemetry_rum_events (id, event, url, ts_ms, occurred_at, payload)
            VALUES (cast(:id as uuid), :event, :url, :ts_ms, :occurred_at, CAST(:payload AS jsonb))
            """
        )
        params = {
            "id": str(uuid.uuid4()),
            "event": name,
            "url": url,
            "ts_ms": ts_ms,
            "occurred_at": occurred_at,
            "payload": json.dumps(payload),
        }
        async with self._engine.begin() as conn:
            await conn.execute(sql, params)

    async def list(self, limit: int) -> list[dict[str, Any]]:
        lim = max(int(limit), 0)
        if lim == 0:
            return []
        sql = text(
            """
            SELECT id::text AS id, event, url, ts_ms, occurred_at, created_at, payload
              FROM telemetry_rum_events
             ORDER BY occurred_at DESC, id DESC
             LIMIT :limit
            """
        )
        async with self._engine.begin() as conn:
            rows = (await conn.execute(sql, {"limit": lim})).mappings().all()
        result: list[dict[str, Any]] = []
        for row in rows:
            payload = dict(row.get("payload") or {})
            ts_value = payload.get("ts") or row.get("ts_ms")
            try:
                ts_ms = int(ts_value)
            except (TypeError, ValueError) as exc:
                logger.debug(
                    "Failed to coerce ts for RUM event %s (value=%r): %s",
                    row.get("id"),
                    ts_value,
                    exc,
                )
                ts_ms = row.get("ts_ms")
            data = payload.get("data")
            created_at = row.get("created_at")
            occurred_at = row.get("occurred_at")
            result.append(
                {
                    "id": row.get("id"),
                    "event": payload.get("event") or row.get("event"),
                    "url": payload.get("url") or row.get("url"),
                    "ts": ts_ms,
                    "data": data,
                    "created_at": (
                        created_at.astimezone(UTC).isoformat() if created_at else None
                    ),
                    "occurred_at": (
                        occurred_at.astimezone(UTC).isoformat() if occurred_at else None
                    ),
                }
            )
        return result


__all__ = ["RumSQLRepository"]
