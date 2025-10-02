from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any

from apps.backend import get_container
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from packages.core.config import to_async_dsn
from packages.core.db import get_async_engine

from ..dtos import ContentStatus, ContentSummary, ContentType
from ..rbac import require_scopes

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/content", tags=["moderation-content"])

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
        except Exception as exc:
            logger.warning("moderation content: failed to ensure node moderation schema: %s", exc)


def _iso(dt: Any) -> str | None:
    if isinstance(dt, str):
        return dt
    if dt is None:
        return None
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")
    try:
        return _iso(datetime.fromisoformat(str(dt)))
    except Exception:
        return None


def _coerce_status(value: Any) -> ContentStatus:
    try:
        if isinstance(value, ContentStatus):
            return value
        return ContentStatus(str(value))
    except Exception:
        return ContentStatus.pending


def _map_action_to_status(action: str) -> ContentStatus:
    act = (action or "").strip().lower()
    if act in {"keep", "allow", "dismiss"}:
        return ContentStatus.resolved
    if act in {"hide", "delete", "remove"}:
        return ContentStatus.hidden
    if act in {"restrict", "limit"}:
        return ContentStatus.restricted
    if act in {"escalate", "review"}:
        return ContentStatus.escalated
    return ContentStatus.pending


def _normalize_actor(actor: Any) -> str | None:
    if actor is None:
        return None
    try:
        actor_str = str(actor).strip()
        return actor_str or None
    except Exception:
        return None


def _get_engine(settings) -> AsyncEngine | None:
    try:
        dsn = to_async_dsn(settings.database_url)
    except Exception:
        logger.debug("moderation content: unable to derive DSN", exc_info=True)
        return None
    if not dsn:
        return None
    try:
        return get_async_engine("moderation-content", url=dsn, future=True)
    except Exception:
        logger.exception("moderation content: failed to create async engine")
        return None


async def _load_content_details(engine: AsyncEngine, content_id: str) -> dict[str, Any] | None:
    try:
        node_id = int(content_id)
    except (TypeError, ValueError):
        return None
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
        "moderation_status_updated_at": _iso(row.get("moderation_status_updated_at")),
        "moderation_history": history,
    }


async def _record_decision(
    engine: AsyncEngine,
    content_id: str,
    action: str,
    reason: Any,
    actor_id: Any,
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    try:
        node_id = int(content_id)
    except (TypeError, ValueError):
        return None
    status = _map_action_to_status(action)
    actor_norm = _normalize_actor(actor_id)
    reason_text = None if reason is None else str(reason)
    payload_json = json.dumps(payload or {}, default=str)
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
        "status": _coerce_status(node_row.get("moderation_status") if node_row else status).value,
        "status_updated_at": _iso(
            node_row.get("moderation_status_updated_at") if node_row else None
        ),
        "history_entry": history_entry,
    }


@router.get(
    "",
    dependencies=[Depends(require_scopes("moderation:content:read"))],
)
async def list_queue(
    type: ContentType | None = None,  # noqa: A002
    status: str | None = None,
    moderation_status: str | None = Query(default=None),
    ai_label: str | None = None,
    has_reports: bool | None = None,
    author_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
    container=Depends(get_container),
) -> dict[str, Any]:
    engine = _get_engine(container.settings)
    if engine is None:
        return {"items": [], "next_cursor": None}
    try:
        offset = int(cursor or 0)
    except Exception:
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
        where.append("n.author_id = cast(:aid as uuid)")
        params["aid"] = str(author_id)
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
            rows = (await conn.execute(text(sql_txt), params)).mappings().all()
    except Exception:
        logger.exception("moderation content: list_queue query failed")
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
        mod_status = _coerce_status(row.get("moderation_status"))
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
                    "moderation_status_updated_at": _iso(row.get("moderation_status_updated_at")),
                    "last_decision": hist_entry,
                },
            }
        )
    next_cursor = str(offset + len(items)) if len(items) == int(limit) else None
    return {"items": items, "next_cursor": next_cursor}


@router.get(
    "/{content_id}",
    response_model=ContentSummary,
    dependencies=[Depends(require_scopes("moderation:content:read"))],
)
async def get_content(content_id: str, container=Depends(get_container)) -> ContentSummary:
    svc = container.platform_moderation.service
    try:
        summary = await svc.get_content(content_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="content_not_found") from exc
    engine = _get_engine(container.settings)
    if engine is None:
        return summary
    try:
        db_info = await _load_content_details(engine, content_id)
    except Exception:
        logger.exception("moderation content: failed to load db details for %s", content_id)
        db_info = None
    if not db_info:
        return summary
    status = _coerce_status(db_info.get("moderation_status"))
    merged_meta = {
        **dict(summary.meta or {}),
        **{
            k: db_info.get(k)
            for k in (
                "node_status",
                "moderation_status",
                "moderation_status_updated_at",
            )
            if db_info.get(k) is not None
        },
    }
    return summary.model_copy(
        update={
            "author_id": db_info.get("author_id") or summary.author_id,
            "created_at": db_info.get("created_at") or summary.created_at,
            "preview": db_info.get("title") or summary.preview,
            "status": status,
            "moderation_history": db_info.get("moderation_history") or summary.moderation_history,
            "meta": merged_meta,
        }
    )


@router.post(
    "/{content_id}/decision",
    dependencies=[Depends(require_scopes("moderation:content:decide:write"))],
)
async def decide_content(
    content_id: str,
    body: dict[str, Any],
    container=Depends(get_container),
) -> dict[str, Any]:
    svc = container.platform_moderation.service
    try:
        result = await svc.decide_content(content_id, body, actor_id=body.get("actor"))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="content_not_found") from exc
    engine = _get_engine(container.settings)
    record = None
    if engine is not None:
        try:
            action_value = body.get("action")
            if not action_value:
                action_value = result.get("decision", {}).get("action")
            record = await _record_decision(
                engine,
                content_id,
                action=str(action_value or ""),
                reason=body.get("reason"),
                actor_id=body.get("actor"),
                payload=body,
            )
        except Exception:
            logger.exception("moderation content: failed to persist decision for %s", content_id)
    response = {"content_id": content_id, **result}
    if record:
        response["moderation_status"] = record.get("status")
        if record.get("history_entry"):
            response.setdefault("decision", result.get("decision", {}))
            response["decision"]["decided_at"] = response["decision"].get("decided_at") or record[
                "history_entry"
            ].get("decided_at")
            response["decision"]["status"] = record["history_entry"].get("status")
        response["db_state"] = record
    return response


@router.patch(
    "/{content_id}",
    dependencies=[Depends(require_scopes("moderation:content:edit:write"))],
)
async def edit_content(
    content_id: str, body: dict[str, Any], container=Depends(get_container)
) -> dict[str, Any]:
    svc = container.platform_moderation.service
    try:
        return await svc.edit_content(content_id, body)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="content_not_found") from exc


__all__ = ["router"]
