from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Iterable
from datetime import datetime
from typing import Any

from sqlalchemy import text as sa_text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

try:
    from packages.core.config import to_async_dsn
    from packages.core.db import get_async_engine
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    to_async_dsn = get_async_engine = None

from ..common import isoformat_utc

logger = logging.getLogger(__name__)


def create_repository(settings) -> TicketsRepository:
    return TicketsRepository(_build_engine(settings))


class TicketsRepository:
    """SQL-backed repository for moderation tickets and messages."""

    def __init__(self, engine: AsyncEngine | None) -> None:
        self._engine = engine
        self._schema_ready = False
        self._schema_lock = asyncio.Lock()

    async def fetch_many(self, ticket_ids: Iterable[str]) -> dict[str, dict[str, Any]]:
        engine = self._engine
        if engine is None:
            return {}
        ids = list({tid for tid in ticket_ids if tid})
        if not ids:
            return {}
        await self._ensure_schema(engine)
        placeholders = ",".join(f":id_{idx}" for idx, _ in enumerate(ids))
        params = {f"id_{idx}": tid for idx, tid in enumerate(ids)}
        sql = (
            "SELECT id, status, priority, assignee_id, updated_at, last_message_at, unread_count, meta"
            " FROM moderation_tickets WHERE id IN (" + placeholders + ")"
        )
        async with engine.connect() as conn:
            rows = (await conn.execute(sa_text(sql), params)).mappings().all()
        return {row["id"]: self._map_ticket(row) for row in rows}

    async def fetch_ticket(self, ticket_id: str) -> dict[str, Any] | None:
        engine = self._engine
        if engine is None:
            return None
        await self._ensure_schema(engine)
        async with engine.connect() as conn:
            row = (
                (
                    await conn.execute(
                        sa_text(
                            "SELECT id, status, priority, assignee_id, updated_at, last_message_at, unread_count, meta"
                            " FROM moderation_tickets WHERE id = :id"
                        ),
                        {"id": ticket_id},
                    )
                )
                .mappings()
                .first()
            )
        return self._map_ticket(row) if row else None

    async def record_ticket_update(
        self,
        ticket_id: str,
        *,
        status: str,
        priority: str,
        assignee_id: str | None,
        updated_at: datetime | None,
        last_message_at: datetime | None,
        unread_count: int,
        meta: dict[str, Any],
    ) -> None:
        engine = self._engine
        if engine is None:
            return
        await self._ensure_schema(engine)
        payload = {
            "id": ticket_id,
            "status": status,
            "priority": priority,
            "assignee_id": assignee_id,
            "updated_at": isoformat_utc(updated_at),
            "last_message_at": isoformat_utc(last_message_at),
            "unread_count": unread_count,
            "meta": json.dumps(meta or {}, ensure_ascii=False),
        }
        try:
            async with engine.begin() as conn:
                await conn.execute(
                    sa_text(
                        """
                        INSERT INTO moderation_tickets (
                            id, status, priority, assignee_id, updated_at, last_message_at, unread_count, meta, created_at, updated_row_at
                        ) VALUES (:id, :status, :priority, :assignee_id, :updated_at, :last_message_at, :unread_count, :meta, COALESCE(:updated_at, CURRENT_TIMESTAMP), CURRENT_TIMESTAMP)
                        ON CONFLICT (id) DO UPDATE SET
                            status = excluded.status,
                            priority = excluded.priority,
                            assignee_id = excluded.assignee_id,
                            updated_at = excluded.updated_at,
                            last_message_at = excluded.last_message_at,
                            unread_count = excluded.unread_count,
                            meta = excluded.meta,
                            updated_row_at = CURRENT_TIMESTAMP
                        """
                    ),
                    payload,
                )
        except (SQLAlchemyError, RuntimeError) as exc:
            logger.exception(
                "tickets repository: failed to persist ticket %s: %s", ticket_id, exc
            )

    async def record_message(
        self,
        *,
        message_id: str,
        ticket_id: str,
        author_id: str,
        text: str,
        created_at: datetime | None,
        internal: bool,
        attachments: list[dict[str, Any]],
        author_name: str | None,
    ) -> dict[str, Any] | None:
        engine = self._engine
        if engine is None:
            return None
        await self._ensure_schema(engine)
        created_text = isoformat_utc(created_at)
        payload = {
            "id": message_id,
            "ticket_id": ticket_id,
            "author_id": author_id,
            "author_name": author_name,
            "text": text,
            "internal": 1 if internal else 0,
            "created_at": created_text,
            "attachments": json.dumps(attachments or [], ensure_ascii=False),
        }
        try:
            async with engine.begin() as conn:
                await conn.execute(
                    sa_text(
                        """
                        INSERT INTO moderation_ticket_messages(
                            id, ticket_id, author_id, author_name, body, internal, created_at, attachments
                        ) VALUES (:id, :ticket_id, :author_id, :author_name, :text, :internal, :created_at, :attachments)
                        ON CONFLICT (id) DO UPDATE SET
                            body = excluded.body,
                            internal = excluded.internal,
                            created_at = excluded.created_at,
                            attachments = excluded.attachments
                        """
                    ),
                    payload,
                )
            return {
                "id": message_id,
                "ticket_id": ticket_id,
                "author_id": author_id,
                "author_name": author_name,
                "text": text,
                "internal": internal,
                "created_at": created_text,
                "attachments": attachments or [],
            }
        except (SQLAlchemyError, RuntimeError) as exc:
            logger.exception(
                "tickets repository: failed to persist message %s: %s", message_id, exc
            )
            return None

    async def list_messages(
        self,
        ticket_id: str,
        *,
        limit: int,
        cursor: str | None,
    ) -> dict[str, Any]:
        engine = self._engine
        if engine is None:
            return {"items": [], "next_cursor": None}
        await self._ensure_schema(engine)
        try:
            offset = max(0, int(cursor or 0))
        except (TypeError, ValueError):
            offset = 0
        query = (
            "SELECT id, ticket_id, author_id, author_name, body, internal, created_at, attachments"
            " FROM moderation_ticket_messages WHERE ticket_id = :ticket_id"
            " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        )
        params = {"ticket_id": ticket_id, "limit": int(limit), "offset": offset}
        async with engine.connect() as conn:
            rows = (await conn.execute(sa_text(query), params)).mappings().all()
        items = [self._map_message(row) for row in rows]
        next_cursor = str(offset + int(limit)) if len(items) == int(limit) else None
        return {"items": items, "next_cursor": next_cursor}

    def _map_ticket(self, row: Any) -> dict[str, Any]:
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
            "priority": row.get("priority"),
            "assignee_id": row.get("assignee_id"),
            "updated_at": row.get("updated_at"),
            "last_message_at": row.get("last_message_at"),
            "unread_count": row.get("unread_count"),
            "meta": meta,
        }

    def _map_message(self, row: Any) -> dict[str, Any]:
        attachments: list[dict[str, Any]] = []
        if row.get("attachments"):
            try:
                attachments = json.loads(row["attachments"])
            except (TypeError, json.JSONDecodeError):
                attachments = []
        return {
            "id": row.get("id"),
            "ticket_id": row.get("ticket_id"),
            "author_id": row.get("author_id"),
            "author_name": row.get("author_name"),
            "text": row.get("body"),
            "internal": bool(row.get("internal")),
            "created_at": row.get("created_at"),
            "attachments": attachments,
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
                        sa_text(
                            """
                            CREATE TABLE IF NOT EXISTS moderation_tickets (
                                id TEXT PRIMARY KEY,
                                status TEXT,
                                priority TEXT,
                                assignee_id TEXT,
                                updated_at TEXT,
                                last_message_at TEXT,
                                unread_count INTEGER DEFAULT 0,
                                meta TEXT,
                                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                                updated_row_at TEXT DEFAULT CURRENT_TIMESTAMP
                            )
                            """
                        )
                    )
                    await conn.execute(
                        sa_text(
                            """
                            CREATE TABLE IF NOT EXISTS moderation_ticket_messages (
                                id TEXT PRIMARY KEY,
                                ticket_id TEXT NOT NULL,
                                author_id TEXT,
                                author_name TEXT,
                                body TEXT,
                                internal INTEGER DEFAULT 0,
                                created_at TEXT,
                                attachments TEXT,
                                CONSTRAINT fk_ticket FOREIGN KEY(ticket_id) REFERENCES moderation_tickets(id) ON DELETE CASCADE
                            )
                            """
                        )
                    )
                self._schema_ready = True
            except (SQLAlchemyError, RuntimeError) as exc:
                logger.exception("tickets repository: failed to ensure schema: %s", exc)


def _build_engine(settings) -> AsyncEngine | None:
    if to_async_dsn is None or get_async_engine is None:
        logger.debug("tickets repository: async engine helpers unavailable")
        return None
    try:
        dsn = to_async_dsn(getattr(settings, "database_url", None))
    except (TypeError, ValueError) as exc:
        logger.debug("tickets repository: invalid DSN: %s", exc)
        return None
    if not dsn:
        return None
    try:
        return get_async_engine("moderation-tickets", url=dsn, future=True)
    except (SQLAlchemyError, RuntimeError, ImportError) as exc:
        logger.error("tickets repository: failed to create engine: %s", exc)
        return None


__all__ = [
    "TicketsRepository",
    "create_repository",
]
