from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Iterable
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

try:
    from packages.core.config import to_async_dsn
    from packages.core.db import get_async_engine
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    to_async_dsn = get_async_engine = None

from packages.core.testing import is_test_mode

from ..common import isoformat_utc

logger = logging.getLogger(__name__)


def create_repository(settings) -> AppealsRepository:
    return AppealsRepository(_build_engine(settings))


def _should_use_sql(settings) -> bool:
    if settings is None:
        return False
    if is_test_mode(settings):
        return False
    return True


class AppealsRepository:
    """SQL-backed repository for moderation appeals."""

    def __init__(self, engine: AsyncEngine | None) -> None:
        self._engine = engine
        self._schema_ready = False
        self._schema_lock = asyncio.Lock()

    async def fetch_many(self, appeal_ids: Iterable[str]) -> dict[str, dict[str, Any]]:
        engine = self._engine
        if engine is None:
            return {}
        ids = list({aid for aid in appeal_ids if aid})
        if not ids:
            return {}
        await self._ensure_schema(engine)
        placeholders = ",".join(f":id_{idx}" for idx, _ in enumerate(ids))
        params = {f"id_{idx}": aid for idx, aid in enumerate(ids)}
        sql = (
            "SELECT id, status, decided_at, decided_by, decision_reason, meta"
            " FROM moderation_appeals WHERE id IN (" + placeholders + ")"
        )
        async with engine.connect() as conn:
            rows = (await conn.execute(text(sql), params)).mappings().all()
        return {row["id"]: self._map_row(row) for row in rows}

    async def fetch_appeal(self, appeal_id: str) -> dict[str, Any] | None:
        engine = self._engine
        if engine is None:
            return None
        await self._ensure_schema(engine)
        async with engine.connect() as conn:
            row = (
                (
                    await conn.execute(
                        text(
                            "SELECT id, status, decided_at, decided_by, decision_reason, meta"
                            " FROM moderation_appeals WHERE id = :id"
                        ),
                        {"id": appeal_id},
                    )
                )
                .mappings()
                .first()
            )
        return self._map_row(row) if row else None

    async def record_decision(
        self,
        appeal_id: str,
        *,
        status: str,
        decided_at: datetime | None,
        decided_by: str | None,
        decision_reason: str | None,
        meta: dict[str, Any],
    ) -> dict[str, Any] | None:
        engine = self._engine
        if engine is None:
            return None
        await self._ensure_schema(engine)
        decided_text = isoformat_utc(decided_at) if decided_at else None
        payload = {
            "id": appeal_id,
            "status": status,
            "decided_at": decided_text,
            "decided_by": decided_by,
            "decision_reason": decision_reason,
            "meta": json.dumps(meta or {}, ensure_ascii=False),
        }
        try:
            async with engine.begin() as conn:
                await conn.execute(
                    text(
                        """
                        INSERT INTO moderation_appeals (
                            id, status, decided_at, decided_by, decision_reason, meta, updated_at
                        ) VALUES (:id, :status, :decided_at, :decided_by, :decision_reason, :meta, CURRENT_TIMESTAMP)
                        ON CONFLICT (id) DO UPDATE SET
                            status = excluded.status,
                            decided_at = excluded.decided_at,
                            decided_by = excluded.decided_by,
                            decision_reason = excluded.decision_reason,
                            meta = excluded.meta,
                            updated_at = CURRENT_TIMESTAMP
                        """
                    ),
                    payload,
                )
        except (SQLAlchemyError, RuntimeError) as exc:
            logger.exception(
                "appeals repository: failed to persist decision %s: %s", appeal_id, exc
            )
            return None
        return {
            "status": status,
            "decided_at": decided_text,
            "decided_by": decided_by,
            "decision_reason": decision_reason,
            "meta": meta,
        }

    def _map_row(self, row: Any) -> dict[str, Any]:
        if not row:
            return {}
        meta: dict[str, Any] = {}
        if row.get("meta"):
            try:
                meta = json.loads(row["meta"])
            except (TypeError, json.JSONDecodeError):
                meta = {}
        return {
            "status": row.get("status"),
            "decided_at": row.get("decided_at"),
            "decided_by": row.get("decided_by"),
            "decision_reason": row.get("decision_reason"),
            "meta": meta,
        }

    async def _ensure_schema(self, engine: AsyncEngine) -> None:
        if self._schema_ready:
            return
        async with self._schema_lock:
            if self._schema_ready:
                return
            try:
                async with engine.begin() as conn:
                    await conn.execute(
                        text(
                            """
                            CREATE TABLE IF NOT EXISTS moderation_appeals (
                                id TEXT PRIMARY KEY,
                                status TEXT,
                                user_id TEXT,
                                target_type TEXT,
                                target_id TEXT,
                                decision_reason TEXT,
                                decided_by TEXT,
                                decided_at TEXT,
                                meta TEXT,
                                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                            )
                            """
                        )
                    )
                self._schema_ready = True
            except (SQLAlchemyError, RuntimeError) as exc:
                logger.exception("appeals repository: failed to ensure schema: %s", exc)


def _build_engine(settings) -> AsyncEngine | None:
    if not _should_use_sql(settings):
        logger.debug("appeals repository: SQL backend disabled; using in-memory mode")
        return None
    if to_async_dsn is None or get_async_engine is None:
        logger.debug("appeals repository: async engine helpers unavailable")
        return None
    database_url = getattr(settings, "database_url", None)
    if not database_url:
        logger.debug(
            "appeals repository: no database_url configured; using in-memory mode"
        )
        return None
    try:
        dsn = to_async_dsn(database_url)
    except (TypeError, ValueError) as exc:
        logger.debug("appeals repository: invalid DSN: %s", exc)
        return None
    if not dsn:
        logger.debug(
            "appeals repository: DSN normalized to empty value; using in-memory mode"
        )
        return None
    try:
        return get_async_engine("moderation-appeals", url=dsn, future=True)
    except (SQLAlchemyError, RuntimeError, ImportError) as exc:
        logger.warning(
            "appeals repository: failed to create engine (fallback to in-memory): %s",
            exc,
        )
        return None


__all__ = [
    "AppealsRepository",
    "create_repository",
]
