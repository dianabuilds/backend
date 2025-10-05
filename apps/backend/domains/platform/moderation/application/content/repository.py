from __future__ import annotations

import asyncio
import json
import logging
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

from ...domain.dtos import ContentStatus, ContentType
from ..common import isoformat_utc, parse_iso_datetime

logger = logging.getLogger(__name__)

_SCHEMA_LOCK = asyncio.Lock()
_SCHEMA_READY = False

_MODERATION_SCHEMA_STATEMENTS = [
    "CREATE EXTENSION IF NOT EXISTS pgcrypto",
    "ALTER TABLE nodes ADD COLUMN IF NOT EXISTS moderation_status text",
    "ALTER TABLE nodes ADD COLUMN IF NOT EXISTS moderation_status_updated_at timestamptz",
    """
    UPDATE nodes
    SET moderation_status = CASE
      WHEN moderation_status IS NOT NULL THEN moderation_status
      WHEN status IN ('published') THEN 'resolved'
      WHEN status IN ('deleted','archived') THEN 'hidden'
      ELSE 'pending'
    END,
        moderation_status_updated_at = COALESCE(moderation_status_updated_at, updated_at)
    WHERE moderation_status IS NULL
    """,
    "ALTER TABLE nodes ALTER COLUMN moderation_status SET DEFAULT 'pending'",
    "CREATE INDEX IF NOT EXISTS ix_nodes_moderation_status ON nodes (moderation_status, updated_at DESC)",
]

_MODERATION_SCHEMA_DO_BLOCKS = [
    """
DO $$
BEGIN
    ALTER TABLE nodes ADD CONSTRAINT nodes_moderation_status_chk CHECK (moderation_status IN ('pending','resolved','hidden','restricted','escalated'));
EXCEPTION
    WHEN duplicate_object THEN NULL;
    WHEN others THEN NULL;
END $$;
""",
    """
DO $$
BEGIN
    ALTER TABLE nodes ALTER COLUMN moderation_status SET NOT NULL;
EXCEPTION
    WHEN others THEN NULL;
END $$;
""",
]


def create_repository(settings) -> ContentRepository:
    return ContentRepository(_build_engine(settings))


def _should_use_sql(settings) -> bool:
    """Decide whether SQL backend should be used based on settings/env."""
    if settings is None:
        return False
    if is_test_mode(settings):
        return False
    return True


class ContentRepository:
    """SQL-backed repository for moderation content metadata."""

    def __init__(self, engine: AsyncEngine | None) -> None:
        self._engine = engine

    @property
    def engine(self) -> AsyncEngine | None:
        return self._engine

    async def list_queue(
        self,
        *,
        content_type: ContentType | None,
        status: str | None,
        moderation_status: str | None,
        ai_label: str | None,
        has_reports: bool | None,
        author_id: str | None,
        date_from: str | None,
        date_to: str | None,
        limit: int,
        cursor: str | None,
    ) -> dict[str, Any]:
        engine = self._engine
        if engine is None:
            return {"items": [], "next_cursor": None}
        try:
            offset = int(cursor or 0)
        except (TypeError, ValueError) as exc:
            logger.debug("moderation content: invalid cursor %r: %s", cursor, exc)
            offset = 0

        where: list[str] = []
        params: dict[str, Any] = {"lim": int(limit), "off": int(offset)}
        if status:
            where.append("n.status = :node_status")
            params["node_status"] = str(status)
        if moderation_status:
            where.append("n.moderation_status = :mod_status")
            params["mod_status"] = str(moderation_status)
        if author_id:
            where.append("n.author_id::text = :aid")
            params["aid"] = str(author_id)
        if content_type:
            where.append("n.content_type = :ctype")
            params["ctype"] = content_type.value
        # ai_label / has_reports will be used when backed storage supports it

        sql_txt = (
            "SELECT n.id, n.author_id::text AS author_id, n.title, n.status AS node_status,"
            " n.created_at, n.moderation_status, n.moderation_status_updated_at,"
            " h.action AS last_action, h.status AS last_status, h.reason AS last_reason,"
            " h.actor_id AS last_actor_id, h.decided_at AS last_decided_at"
            " FROM nodes n"
            " LEFT JOIN LATERAL (SELECT action, status, reason, actor_id, decided_at"
            "                   FROM node_moderation_history"
            "                   WHERE node_id = n.id"
            "                   ORDER BY decided_at DESC LIMIT 1) h ON true"
        )
        if where:
            sql_txt += " WHERE " + " AND ".join(where)
        sql_txt += (
            " ORDER BY n.moderation_status_updated_at DESC NULLS LAST,"
            " n.updated_at DESC NULLS LAST, n.id DESC LIMIT :lim OFFSET :off"
        )

        try:
            async with engine.begin() as conn:
                await _ensure_nodes_moderation_schema(conn)
                rows = (await conn.execute(text(sql_txt), params)).mappings().all()
        except (SQLAlchemyError, RuntimeError) as exc:
            logger.exception("moderation content: list_queue query failed: %s", exc)
            return {"items": [], "next_cursor": None}

        items: list[dict[str, Any]] = []
        for row in rows:
            hist_entry = None
            if row.get("last_action"):
                hist_entry = {
                    "action": row.get("last_action"),
                    "status": row.get("last_status"),
                    "reason": row.get("last_reason"),
                    "actor": _normalize_actor(row.get("last_actor_id")),
                    "decided_at": _iso(row.get("last_decided_at")),
                }
            mod_status = coerce_status(row.get("moderation_status"))
            items.append(
                {
                    "id": str(row.get("id")),
                    "type": "node",
                    "author_id": row.get("author_id") or "",
                    "created_at": _iso(row.get("created_at")),
                    "preview": row.get("title") or "",
                    "ai_labels": [],
                    "complaints_count": 0,
                    "status": mod_status.value,
                    "moderation_history": [hist_entry] if hist_entry else [],
                    "reports": [],
                    "meta": {
                        "node_status": row.get("node_status"),
                        "moderation_status": mod_status.value,
                        "moderation_status_updated_at": _iso(
                            row.get("moderation_status_updated_at")
                        ),
                        "last_decision": hist_entry,
                    },
                }
            )
        next_cursor = str(offset + len(items)) if len(items) == int(limit) else None
        return {"items": items, "next_cursor": next_cursor}

    async def load_content_details(self, content_id: str) -> dict[str, Any] | None:
        engine = self._engine
        if engine is None:
            return None
        try:
            node_id = int(content_id)
        except (TypeError, ValueError):
            return None

        try:
            async with engine.begin() as conn:
                await _ensure_nodes_moderation_schema(conn)
                row = (
                    (
                        await conn.execute(
                            text(
                                "SELECT id, author_id::text AS author_id, title, status AS node_status, created_at,"
                                " moderation_status, moderation_status_updated_at"
                                " FROM nodes WHERE id = :id"
                            ),
                            {"id": node_id},
                        )
                    )
                    .mappings()
                    .first()
                )
                if not row:
                    return None
                history_rows = (
                    (
                        await conn.execute(
                            text(
                                "SELECT action, status, reason, actor_id, decided_at, payload"
                                " FROM node_moderation_history WHERE node_id = :id"
                                " ORDER BY decided_at DESC, action ASC LIMIT 50"
                            ),
                            {"id": node_id},
                        )
                    )
                    .mappings()
                    .all()
                )
        except (SQLAlchemyError, RuntimeError) as exc:
            logger.exception(
                "moderation content: failed to load db details for %s: %s",
                content_id,
                exc,
            )
            return None

        history = [
            {
                "action": h.get("action"),
                "status": h.get("status"),
                "reason": h.get("reason"),
                "actor": _normalize_actor(h.get("actor_id")),
                "decided_at": _iso(h.get("decided_at")),
                "payload": h.get("payload"),
            }
            for h in history_rows
        ]
        return {
            "id": str(row.get("id")),
            "author_id": row.get("author_id"),
            "title": row.get("title"),
            "node_status": row.get("node_status"),
            "created_at": _iso(row.get("created_at")),
            "moderation_status": row.get("moderation_status"),
            "moderation_status_updated_at": _iso(
                row.get("moderation_status_updated_at")
            ),
            "moderation_history": history,
        }

    async def record_decision(
        self,
        content_id: str,
        *,
        action: str,
        reason: Any,
        actor_id: Any,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        engine = self._engine
        if engine is None:
            return None
        try:
            node_id = int(content_id)
        except (TypeError, ValueError):
            return None
        status = _map_action_to_status(action)
        actor_norm = _normalize_actor(actor_id)
        reason_text = None if reason is None else str(reason)
        payload_json = json.dumps(payload or {}, default=str)

        try:
            async with engine.begin() as conn:
                await _ensure_nodes_moderation_schema(conn)
                await conn.execute(
                    text(
                        "UPDATE nodes SET moderation_status = :status,"
                        " moderation_status_updated_at = now() WHERE id = :id"
                    ),
                    {"status": status.value, "id": node_id},
                )
                hist_row = (
                    (
                        await conn.execute(
                            text(
                                "INSERT INTO node_moderation_history"
                                " (node_id, action, status, reason, actor_id, decided_at, payload)"
                                " VALUES (:node_id, :action, :status, :reason, :actor_id, now(), :payload)"
                                " RETURNING action, status, reason, actor_id, decided_at, payload"
                            ),
                            {
                                "node_id": node_id,
                                "action": action,
                                "status": status.value,
                                "reason": reason_text,
                                "actor_id": actor_norm,
                                "payload": payload_json,
                            },
                        )
                    )
                    .mappings()
                    .first()
                )
                node_row = (
                    (
                        await conn.execute(
                            text(
                                "SELECT moderation_status, moderation_status_updated_at"
                                " FROM nodes WHERE id = :id"
                            ),
                            {"id": node_id},
                        )
                    )
                    .mappings()
                    .first()
                )
        except (SQLAlchemyError, RuntimeError) as exc:
            logger.exception(
                "moderation content: failed to persist decision for %s: %s",
                content_id,
                exc,
            )
            return None

        history_entry = None
        if hist_row:
            history_entry = {
                "action": hist_row.get("action"),
                "status": hist_row.get("status"),
                "reason": hist_row.get("reason"),
                "actor": _normalize_actor(hist_row.get("actor_id")),
                "decided_at": _iso(hist_row.get("decided_at")),
                "payload": hist_row.get("payload"),
            }
        return {
            "status": coerce_status(
                node_row.get("moderation_status") if node_row else status
            ).value,
            "status_updated_at": _iso(
                node_row.get("moderation_status_updated_at") if node_row else None
            ),
            "history_entry": history_entry,
        }


def coerce_status(value: Any) -> ContentStatus:
    try:
        if isinstance(value, ContentStatus):
            return value
        return ContentStatus(str(value))
    except (TypeError, ValueError) as exc:
        logger.debug("moderation content: unknown status %r: %s", value, exc)
        return ContentStatus.pending


def _build_engine(settings) -> AsyncEngine | None:
    if not _should_use_sql(settings):
        logger.debug(
            "moderation content: SQL repository disabled; using in-memory mode"
        )
        return None
    if to_async_dsn is None or get_async_engine is None:
        logger.debug(
            "moderation content: database helpers are unavailable; falling back to in-memory mode"
        )
        return None
    database_url = getattr(settings, "database_url", None)
    if not database_url:
        logger.debug(
            "moderation content: no database_url configured; using in-memory mode"
        )
        return None
    try:
        dsn = to_async_dsn(database_url)
    except (TypeError, ValueError) as exc:
        logger.debug("moderation content: unable to derive DSN: %s", exc, exc_info=True)
        return None
    if not dsn:
        logger.debug(
            "moderation content: DSN normalized to empty value; using in-memory mode"
        )
        return None
    try:
        return get_async_engine("moderation-content", url=dsn, future=True)
    except (SQLAlchemyError, RuntimeError, ImportError) as exc:
        logger.warning(
            "moderation content: failed to create async engine (fallback to in-memory): %s",
            exc,
        )
        return None


def _iso(value: Any) -> str | None:
    if isinstance(value, str):
        parsed = parse_iso_datetime(value, logger_override=logger)
        return isoformat_utc(parsed) if parsed else value
    return isoformat_utc(value)


async def _apply_nodes_moderation_schema(conn) -> None:
    for stmt in _MODERATION_SCHEMA_STATEMENTS:
        await conn.execute(text(stmt))
    for stmt in _MODERATION_SCHEMA_DO_BLOCKS:
        await conn.execute(text(stmt))


async def _ensure_nodes_moderation_schema(conn) -> None:
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return
    async with _SCHEMA_LOCK:
        if _SCHEMA_READY:
            return
        try:
            await _apply_nodes_moderation_schema(conn)
            col_check = await conn.execute(
                text(
                    "SELECT 1 FROM information_schema.columns"
                    " WHERE table_schema = 'public' AND table_name = 'nodes' AND column_name = 'moderation_status'"
                )
            )
            tbl_check = await conn.execute(
                text(
                    "SELECT 1 FROM information_schema.tables"
                    " WHERE table_schema = 'public' AND table_name = 'node_moderation_history'"
                )
            )
            if col_check.scalar() is not None and tbl_check.scalar() is not None:
                _SCHEMA_READY = True
        except (TimeoutError, SQLAlchemyError, RuntimeError, OSError) as exc:
            logger.warning(
                "moderation content: failed to ensure node moderation schema: %s", exc
            )


def _normalize_actor(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str) and value.startswith("user:"):
        return value
    if isinstance(value, str):
        return f"user:{value}"
    return str(value)


def _map_action_to_status(action: str) -> ContentStatus:
    action_norm = str(action or "").lower()
    if action_norm in {"keep", "allow", "dismiss"}:
        return ContentStatus.resolved
    if action_norm in {"hide", "delete", "remove"}:
        return ContentStatus.hidden
    if action_norm in {"restrict", "limit"}:
        return ContentStatus.restricted
    if action_norm in {"escalate", "review"}:
        return ContentStatus.escalated
    return ContentStatus.pending


__all__ = [
    "ContentRepository",
    "create_repository",
    "coerce_status",
]
