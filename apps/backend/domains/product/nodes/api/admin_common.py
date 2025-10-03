from __future__ import annotations

import csv
import json
import logging
from datetime import UTC, datetime, timedelta
from io import StringIO
from typing import Any

from fastapi import HTTPException, Request
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.product.nodes.application.ports import (  # type: ignore[import-not-found]
    NodeCommentBanDTO,
    NodeCommentDTO,
)
from packages.core.config import to_async_dsn  # type: ignore[import-not-found]
from packages.core.db import get_async_engine  # type: ignore[import-not-found]

logger = logging.getLogger(__name__)


async def _ensure_engine(container) -> AsyncEngine | None:
    try:
        dsn = to_async_dsn(container.settings.database_url)
    except (ValidationError, ValueError, TypeError) as exc:
        logger.warning("nodes_admin_invalid_database_dsn", exc_info=exc)
        return None
    if not dsn:
        return None
    if "?" in dsn:
        dsn = dsn.split("?", 1)[0]
    try:
        return get_async_engine("nodes-admin", url=dsn, future=True)
    except SQLAlchemyError as exc:
        logger.error("nodes_admin_engine_init_failed", exc_info=exc)
        return None


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    try:
        parsed = datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None
    return _iso(parsed)


_ALLOWED_MODERATION_STATUSES = {
    "pending",
    "resolved",
    "hidden",
    "restricted",
    "escalated",
}
_DECISION_STATUS_MAP = {
    "keep": "resolved",
    "hide": "hidden",
    "delete": "hidden",
    "restrict": "restricted",
    "escalate": "escalated",
    "review": "pending",
}


def _normalize_moderation_status(value: Any) -> str:
    try:
        result = str(value or "").strip().lower()
    except (AttributeError, TypeError, ValueError):
        result = ""
    if result not in _ALLOWED_MODERATION_STATUSES:
        return "pending"
    return result


def _decision_to_status(action: str) -> str:
    return _DECISION_STATUS_MAP.get(action, "pending")


_COMMENT_STATUS_ORDER = ["pending", "published", "hidden", "deleted", "blocked"]
_COMMENT_STATUS_SET = set(_COMMENT_STATUS_ORDER)


SYSTEM_ACTOR_ID = "00000000-0000-0000-0000-000000000000"


def _normalize_comment_status_filter(
    statuses: Any,
    *,
    include_deleted: bool,
) -> list[str]:
    if not statuses:
        base = list(_COMMENT_STATUS_ORDER)
        if not include_deleted:
            base = [status for status in base if status != "deleted"]
        return base
    result: list[str] = []
    seen: set[str] = set()
    values = statuses
    if not isinstance(values, (list, tuple, set)):
        values = [values]
    for raw in values:
        try:
            normalized = str(raw or "").strip().lower()
        except (TypeError, ValueError):
            continue
        if normalized == "deleted" and not include_deleted:
            continue
        if normalized in _COMMENT_STATUS_SET and normalized not in seen:
            result.append(normalized)
            seen.add(normalized)
    if not result:
        base = list(_COMMENT_STATUS_ORDER)
        if not include_deleted:
            base = [status for status in base if status != "deleted"]
        return base
    return result


def _parse_query_datetime(raw: str | None, *, field: str) -> datetime | None:
    if raw is None:
        return None
    value = str(raw).strip()
    if not value:
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"{field}_invalid") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _coerce_metadata(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        try:
            return json.loads(json.dumps(raw))
        except (TypeError, ValueError):
            return dict(raw)
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except ValueError:
            return {}
        if isinstance(parsed, dict):
            return parsed
        return {}
    return {}


def _extract_comment_history(metadata: dict[str, Any]) -> list[dict[str, Any]]:
    history_raw = metadata.get("history")
    history: list[dict[str, Any]] = []
    if isinstance(history_raw, list):
        for entry in history_raw:
            if not isinstance(entry, dict):
                continue
            record = {
                "status": str(entry.get("status") or ""),
                "actor_id": str(entry.get("actor_id")) if entry.get("actor_id") else None,
                "reason": entry.get("reason"),
                "at": _iso(entry.get("at")),
            }
            history.append(record)
    return history


def _comment_record_to_payload(
    *,
    comment_id: int,
    node_id: int,
    author_id: str,
    parent_comment_id: int | None,
    depth: int,
    content: str,
    status: str,
    metadata: Any,
    created_at: Any,
    updated_at: Any,
    children_count: int | None = None,
) -> dict[str, Any]:
    meta = _coerce_metadata(metadata)
    history = _extract_comment_history(meta)
    payload: dict[str, Any] = {
        "id": str(comment_id),
        "node_id": str(node_id),
        "author_id": str(author_id),
        "parent_comment_id": str(parent_comment_id) if parent_comment_id is not None else None,
        "depth": int(depth),
        "content": content,
        "status": str(status),
        "metadata": meta,
        "history": history,
        "created_at": _iso(created_at),
        "updated_at": _iso(updated_at),
    }
    if children_count is not None:
        payload["children_count"] = int(children_count)
    return payload


def _comment_dto_to_dict(
    dto: NodeCommentDTO, *, children_count: int | None = None
) -> dict[str, Any]:
    return _comment_record_to_payload(
        comment_id=dto.id,
        node_id=dto.node_id,
        author_id=dto.author_id,
        parent_comment_id=dto.parent_comment_id,
        depth=dto.depth,
        content=dto.content,
        status=dto.status,
        metadata=dto.metadata,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
        children_count=children_count,
    )


def _comment_row_to_dict(row) -> dict[str, Any]:
    parent_raw = row.get("parent_comment_id")
    parent_id = None if parent_raw is None else int(parent_raw)
    children_raw = row.get("children_count")
    children_count = None
    if children_raw is not None:
        try:
            children_count = int(children_raw)
        except (TypeError, ValueError):
            children_count = None
    return _comment_record_to_payload(
        comment_id=int(row["id"]),
        node_id=int(row["node_id"]),
        author_id=str(row.get("author_id")),
        parent_comment_id=parent_id,
        depth=int(row["depth"]),
        content=row.get("content"),
        status=str(row.get("status")),
        metadata=row.get("metadata"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
        children_count=children_count,
    )


def _ban_to_dict(ban: NodeCommentBanDTO) -> dict[str, Any]:
    return {
        "node_id": str(ban.node_id),
        "target_user_id": ban.target_user_id,
        "set_by": ban.set_by,
        "reason": ban.reason,
        "created_at": _iso(ban.created_at),
    }


def _extract_actor_id(request: Request) -> str | None:
    try:
        ctx = getattr(request.state, "auth_context", None)
    except AttributeError:
        ctx = None
    if isinstance(ctx, dict):
        candidate = ctx.get("actor_id") or ctx.get("user_id") or ctx.get("sub")
        if candidate:
            return str(candidate)
    header_actor = request.headers.get("X-Actor-Id") or request.headers.get("x-actor-id")
    if header_actor:
        candidate = header_actor.strip()
        if candidate:
            return candidate
    return None


async def _emit_admin_activity(
    container,
    *,
    event: str | None = None,
    payload: dict[str, Any] | None = None,
    key: str | None = None,
    event_context: dict[str, Any] | None = None,
    audit_action: str | None = None,
    audit_actor: str | None = None,
    audit_resource_type: str | None = None,
    audit_resource_id: str | None = None,
    audit_reason: str | None = None,
    audit_extra: dict[str, Any] | None = None,
) -> None:
    if event and payload is not None:
        nodes_service = getattr(container, "nodes_service", None)
        safe_publish = getattr(nodes_service, "_safe_publish", None) if nodes_service else None
        context_payload: dict[str, Any] = {"source": "nodes_admin_api"}
        if event_context:
            context_payload.update(event_context)
        if callable(safe_publish):
            safe_publish(event, payload, key=key, context=context_payload)
        else:
            try:
                container.events.publish(event, payload, key=key)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "nodes_admin_event_publish_failed",
                    extra={"event": event, "key": key, "context": context_payload},
                    exc_info=exc,
                )
    if audit_action:
        audit_container = getattr(container, "audit", None)
        service = getattr(audit_container, "service", None) if audit_container else None
        log_fn = getattr(service, "log", None) if service else None
        if callable(log_fn):
            try:
                await log_fn(
                    actor_id=audit_actor,
                    action=audit_action,
                    resource_type=audit_resource_type,
                    resource_id=audit_resource_id,
                    reason=audit_reason,
                    extra=audit_extra,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "nodes_admin_audit_failed",
                    extra={"action": audit_action, "resource_id": audit_resource_id},
                    exc_info=exc,
                )


def _status_summary_from_counts(counts: dict[str, int]) -> dict[str, Any]:
    summary = {status: int(counts.get(status, 0)) for status in _COMMENT_STATUS_ORDER}
    total = sum(summary.values())
    return {"total": total, "by_status": summary}


def _build_status_condition(
    alias: str,
    statuses: list[str],
    params: dict[str, Any],
    *,
    prefix: str,
) -> str:
    if not statuses:
        return ""
    placeholders: list[str] = []
    for idx, status in enumerate(statuses):
        key = f"{prefix}_{idx}"
        params[key] = status
        placeholders.append(f":{key}")
    return f"{alias}.status IN (" + ", ".join(placeholders) + ")"


def _append_comment_filters(
    *,
    conditions: list[str],
    params: dict[str, Any],
    alias: str,
    author_id: str | None,
    created_from: datetime | None,
    created_to: datetime | None,
    search: str | None,
    prefix: str,
) -> None:
    if author_id:
        key = f"{prefix}_author_id"
        conditions.append(f"{alias}.author_id = cast(:{key} as uuid)")
        params[key] = str(author_id)
    if created_from:
        key = f"{prefix}_created_from"
        conditions.append(f"{alias}.created_at >= :{key}")
        params[key] = created_from
    if created_to:
        key = f"{prefix}_created_to"
        conditions.append(f"{alias}.created_at <= :{key}")
        params[key] = created_to
    if search:
        key = f"{prefix}_search"
        key_exact = f"{prefix}_search_exact"
        conditions.append(
            f"({alias}.content ILIKE :{key} OR cast({alias}.id as text) = :{key_exact})"
        )
        params[key] = f"%{search}%"
        params[key_exact] = str(search)


def _ensure_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    try:
        parsed = datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


async def _fetch_engagement_summary(engine: AsyncEngine, node_id: int) -> dict[str, Any]:
    summary_sql = text(
        """
        SELECT
            n.id,
            n.slug,
            n.title,
            n.author_id::text AS author_id,
            n.status,
            n.is_public,
            n.created_at,
            n.updated_at,
            n.views_count,
            n.reactions_like_count,
            n.comments_disabled,
            n.comments_locked_by::text AS comments_locked_by,
            n.comments_locked_at,
            stats.total_comments,
            stats.pending_count,
            stats.published_count,
            stats.hidden_count,
            stats.deleted_count,
            stats.blocked_count,
            stats.last_comment_created_at,
            stats.last_comment_updated_at,
            stats.bans_count
        FROM nodes n
        LEFT JOIN LATERAL (
            SELECT
                COUNT(*)::bigint AS total_comments,
                COALESCE(SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END), 0)::bigint AS pending_count,
                COALESCE(SUM(CASE WHEN status = 'published' THEN 1 ELSE 0 END), 0)::bigint AS published_count,
                COALESCE(SUM(CASE WHEN status = 'hidden' THEN 1 ELSE 0 END), 0)::bigint AS hidden_count,
                COALESCE(SUM(CASE WHEN status = 'deleted' THEN 1 ELSE 0 END), 0)::bigint AS deleted_count,
                COALESCE(SUM(CASE WHEN status = 'blocked' THEN 1 ELSE 0 END), 0)::bigint AS blocked_count,
                MAX(created_at) AS last_comment_created_at,
                MAX(updated_at) AS last_comment_updated_at,
                (SELECT COUNT(*)::bigint FROM node_comment_bans b WHERE b.node_id = n.id) AS bans_count
            FROM node_comments
            WHERE node_id = n.id
        ) AS stats ON TRUE
        WHERE n.id = :node_id
        """
    )
    async with engine.begin() as conn:
        row = (await conn.execute(summary_sql, {"node_id": int(node_id)})).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="not_found")
    counts_map = {
        "pending": int(row.get("pending_count") or 0),
        "published": int(row.get("published_count") or 0),
        "hidden": int(row.get("hidden_count") or 0),
        "deleted": int(row.get("deleted_count") or 0),
        "blocked": int(row.get("blocked_count") or 0),
    }
    comments_summary = _status_summary_from_counts(counts_map)
    comments_summary["disabled"] = bool(row.get("comments_disabled"))
    locked_by = row.get("comments_locked_by")
    comments_summary["locked"] = locked_by is not None
    comments_summary["locked_by"] = locked_by
    comments_summary["locked_at"] = _iso(row.get("comments_locked_at"))
    comments_summary["last_comment_created_at"] = _iso(row.get("last_comment_created_at"))
    comments_summary["last_comment_updated_at"] = _iso(row.get("last_comment_updated_at"))
    comments_summary["bans_count"] = int(row.get("bans_count") or 0)
    node_id_str = str(row.get("id"))
    summary = {
        "id": node_id_str,
        "slug": row.get("slug"),
        "title": row.get("title"),
        "status": row.get("status"),
        "is_public": bool(row.get("is_public")),
        "author_id": row.get("author_id"),
        "views_count": int(row.get("views_count") or 0),
        "reactions": {"like": int(row.get("reactions_like_count") or 0)},
        "comments": comments_summary,
        "created_at": _iso(row.get("created_at")),
        "updated_at": _iso(row.get("updated_at")),
    }
    summary["links"] = {
        "moderation": f"/v1/admin/nodes/{node_id_str}/moderation",
        "comments": f"/v1/admin/nodes/{node_id_str}/comments",
        "analytics": f"/v1/admin/nodes/{node_id_str}/analytics",
        "bans": f"/v1/admin/nodes/{node_id_str}/comment-bans",
    }
    return summary


async def _fetch_comment_collection(
    engine: AsyncEngine,
    *,
    node_id: int,
    view: str,
    parent_id: int | None,
    statuses: list[str],
    author_id: str | None,
    created_from: datetime | None,
    created_to: datetime | None,
    search: str | None,
    limit: int,
    offset: int,
    order: str,
) -> dict[str, Any]:
    alias = "c"
    order_clause = "DESC" if order == "desc" else "ASC"
    async with engine.begin() as conn:
        params: dict[str, Any] = {"node_id": int(node_id)}
        conditions: list[str] = [f"{alias}.node_id = :node_id"]
        status_clause = _build_status_condition(alias, statuses, params, prefix="status")
        if status_clause:
            conditions.append(status_clause)
        view_mode = view.lower()
        if view_mode == "roots":
            conditions.append(f"{alias}.parent_comment_id IS NULL")
        elif view_mode == "children":
            if parent_id is None:
                raise HTTPException(status_code=400, detail="parent_id_required")
            parent_row = (
                (
                    await conn.execute(
                        text("SELECT node_id FROM node_comments WHERE id = :parent_id"),
                        {"parent_id": int(parent_id)},
                    )
                )
                .mappings()
                .first()
            )
            if parent_row is None or int(parent_row["node_id"]) != int(node_id):
                raise HTTPException(status_code=404, detail="comment_not_found")
            conditions.append(f"{alias}.parent_comment_id = :parent_id")
            params["parent_id"] = int(parent_id)
        elif view_mode == "all":
            pass
        else:
            raise HTTPException(status_code=400, detail="view_invalid")
        _append_comment_filters(
            conditions=conditions,
            params=params,
            alias=alias,
            author_id=author_id,
            created_from=created_from,
            created_to=created_to,
            search=search,
            prefix="filter",
        )
        where_clause = " AND ".join(conditions)
        counts_query = text(
            f"SELECT {alias}.status AS status, COUNT(*)::bigint AS count FROM node_comments {alias} WHERE {where_clause} GROUP BY {alias}.status"
        )
        counts_rows = (await conn.execute(counts_query, params)).mappings().all()
        counts_map = {row["status"]: int(row["count"] or 0) for row in counts_rows}
        summary = _status_summary_from_counts(counts_map)
        total = summary["total"]
        data_params = dict(params)
        data_params["limit"] = int(limit)
        data_params["offset"] = int(offset)
        data_query = text(
            f"""
            SELECT {alias}.id,
                   {alias}.node_id,
                   {alias}.author_id::text AS author_id,
                   {alias}.parent_comment_id,
                   {alias}.depth,
                   {alias}.content,
                   {alias}.status,
                   {alias}.metadata,
                   {alias}.created_at,
                   {alias}.updated_at,
                   (
                       SELECT COUNT(*)
                         FROM node_comments child
                        WHERE child.parent_comment_id = {alias}.id
                   ) AS children_count
              FROM node_comments {alias}
             WHERE {where_clause}
             ORDER BY {alias}.created_at {order_clause}, {alias}.id {order_clause}
             LIMIT :limit OFFSET :offset
            """
        )
        rows = (await conn.execute(data_query, data_params)).mappings().all()
    items = [_comment_row_to_dict(row) for row in rows]
    return {
        "items": items,
        "summary": summary,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + len(items)) < total,
    }


async def _fetch_comment_thread(
    engine: AsyncEngine,
    *,
    node_id: int,
    root_id: int,
    statuses: list[str],
    author_id: str | None,
    created_from: datetime | None,
    created_to: datetime | None,
    search: str | None,
    order: str,
) -> dict[str, Any]:
    alias = "t"
    order_clause = "ASC" if order == "asc" else "DESC"
    async with engine.begin() as conn:
        parent_row = (
            (
                await conn.execute(
                    text("SELECT node_id FROM node_comments WHERE id = :root_id"),
                    {"root_id": int(root_id)},
                )
            )
            .mappings()
            .first()
        )
        if parent_row is None or int(parent_row["node_id"]) != int(node_id):
            raise HTTPException(status_code=404, detail="comment_not_found")
        params: dict[str, Any] = {"root_id": int(root_id), "node_id": int(node_id)}
        conditions: list[str] = ["1=1"]
        status_clause = _build_status_condition(alias, statuses, params, prefix="thread_status")
        if status_clause:
            conditions.append(status_clause)
        _append_comment_filters(
            conditions=conditions,
            params=params,
            alias=alias,
            author_id=author_id,
            created_from=created_from,
            created_to=created_to,
            search=search,
            prefix="thread",
        )
        where_clause = " AND ".join(conditions)
        query = text(
            f"""
            WITH RECURSIVE thread AS (
                SELECT c.*
                  FROM node_comments c
                 WHERE c.id = :root_id
                   AND c.node_id = :node_id
                UNION ALL
                SELECT child.*
                  FROM node_comments child
                  JOIN thread parent ON child.parent_comment_id = parent.id
            )
            SELECT t.id,
                   t.node_id,
                   t.author_id::text AS author_id,
                   t.parent_comment_id,
                   t.depth,
                   t.content,
                   t.status,
                   t.metadata,
                   t.created_at,
                   t.updated_at,
                   (
                       SELECT COUNT(*)
                         FROM node_comments child
                        WHERE child.parent_comment_id = t.id
                   ) AS children_count
              FROM thread t
             WHERE {where_clause}
             ORDER BY t.created_at {order_clause}, t.id {order_clause}
            """
        )
        rows = (await conn.execute(query, params)).mappings().all()
        counts_query = text(
            f"""
            WITH RECURSIVE thread AS (
                SELECT c.*
                  FROM node_comments c
                 WHERE c.id = :root_id
                   AND c.node_id = :node_id
                UNION ALL
                SELECT child.*
                  FROM node_comments child
                  JOIN thread parent ON child.parent_comment_id = parent.id
            )
            SELECT status, COUNT(*)::bigint AS count
              FROM thread
             WHERE {where_clause}
             GROUP BY status
            """
        )
        counts_rows = (await conn.execute(counts_query, params)).mappings().all()
    counts_map = {row["status"]: int(row["count"] or 0) for row in counts_rows}
    summary = _status_summary_from_counts(counts_map)
    items = [_comment_row_to_dict(row) for row in rows]
    total = summary["total"]
    return {
        "items": items,
        "summary": summary,
        "total": total,
        "limit": total,
        "offset": 0,
        "has_more": False,
    }


async def _fetch_comments_data(
    engine: AsyncEngine,
    *,
    node_id: int,
    view: str,
    parent_id: int | None,
    statuses: list[str],
    author_id: str | None,
    created_from: datetime | None,
    created_to: datetime | None,
    search: str | None,
    limit: int,
    offset: int,
    order: str,
) -> dict[str, Any]:
    view_mode = (view or "roots").lower()
    if view_mode == "thread":
        if parent_id is None:
            raise HTTPException(status_code=400, detail="thread_id_required")
        return await _fetch_comment_thread(
            engine,
            node_id=node_id,
            root_id=int(parent_id),
            statuses=statuses,
            author_id=author_id,
            created_from=created_from,
            created_to=created_to,
            search=search,
            order=order,
        )
    return await _fetch_comment_collection(
        engine,
        node_id=node_id,
        view=view_mode,
        parent_id=parent_id,
        statuses=statuses,
        author_id=author_id,
        created_from=created_from,
        created_to=created_to,
        search=search,
        limit=limit,
        offset=offset,
        order=order,
    )


async def _fetch_analytics(
    engine: AsyncEngine,
    *,
    node_id: int,
    start: datetime | None,
    end: datetime | None,
    limit: int,
) -> dict[str, Any]:
    start_utc = _ensure_utc(start)
    end_utc = _ensure_utc(end)
    start_date = start_utc.date() if start_utc else None
    end_date = end_utc.date() if end_utc else None
    reactions_end = end_utc + timedelta(days=1) if end_utc else None
    now = datetime.now(UTC)
    async with engine.begin() as conn:
        views_conditions = ["node_id = :node_id"]
        views_params: dict[str, Any] = {"node_id": int(node_id), "limit": int(limit)}
        if start_date:
            views_conditions.append("bucket_date >= :start_date")
            views_params["start_date"] = start_date
        if end_date:
            views_conditions.append("bucket_date <= :end_date")
            views_params["end_date"] = end_date
        views_where = " AND ".join(views_conditions)
        views_sql = text(
            f"""
            SELECT bucket_date, views, updated_at
              FROM node_views_daily
             WHERE {views_where}
             ORDER BY bucket_date DESC
             LIMIT :limit
            """
        )
        views_rows = (await conn.execute(views_sql, views_params)).mappings().all()
        views_total = sum(int(row["views"] or 0) for row in views_rows)
        latest_views_updated = None
        if views_rows:
            latest_views_updated = max(
                row["updated_at"] for row in views_rows if row["updated_at"] is not None
            )
        buckets = [
            {
                "bucket_date": row["bucket_date"].isoformat(),
                "views": int(row["views"] or 0),
            }
            for row in reversed(views_rows)
        ]
        reactions_conditions = ["node_id = :node_id"]
        reactions_params: dict[str, Any] = {"node_id": int(node_id)}
        if start_utc:
            reactions_conditions.append("created_at >= :reaction_start")
            reactions_params["reaction_start"] = start_utc
        if reactions_end:
            reactions_conditions.append("created_at < :reaction_end")
            reactions_params["reaction_end"] = reactions_end
        reactions_where = " AND ".join(reactions_conditions)
        reactions_sql = text(
            f"""
            SELECT reaction_type,
                   COUNT(*)::bigint AS count,
                   MAX(created_at) AS last_created_at
              FROM node_reactions
             WHERE {reactions_where}
             GROUP BY reaction_type
            """
        )
        reactions_rows = (await conn.execute(reactions_sql, reactions_params)).mappings().all()
        reactions_totals = {
            str(row["reaction_type"]): int(row["count"] or 0) for row in reactions_rows
        }
        latest_reaction_at = None
        if reactions_rows:
            latest_reaction_at = max(
                row["last_created_at"]
                for row in reactions_rows
                if row["last_created_at"] is not None
            )
        comments_conditions = ["node_id = :node_id"]
        comments_params: dict[str, Any] = {"node_id": int(node_id)}
        if start_utc:
            comments_conditions.append("created_at >= :comments_start")
            comments_params["comments_start"] = start_utc
        if reactions_end:
            comments_conditions.append("created_at < :comments_end")
            comments_params["comments_end"] = reactions_end
        comments_where = " AND ".join(comments_conditions)
        comments_sql = text(
            f"""
            SELECT status,
                   COUNT(*)::bigint AS count,
                   MAX(created_at) AS last_created_at
              FROM node_comments
             WHERE {comments_where}
             GROUP BY status
            """
        )
        comments_rows = (await conn.execute(comments_sql, comments_params)).mappings().all()
    comments_counts = {row["status"]: int(row["count"] or 0) for row in comments_rows}
    comments_summary = _status_summary_from_counts(comments_counts)
    comments_last_created: datetime | None = None
    if comments_rows:
        comments_last_created = max(
            row["last_created_at"] for row in comments_rows if row["last_created_at"] is not None
        )
    raw_points: list[datetime | None] = [
        _ensure_utc(latest_views_updated),
        _ensure_utc(latest_reaction_at),
        _ensure_utc(comments_last_created),
    ]
    latest_points: list[datetime] = [ts for ts in raw_points if ts is not None]
    delay_payload: dict[str, Any] | None = None
    if latest_points:
        latest_ts = max(latest_points)
        delay_seconds = max(0, int((now - latest_ts).total_seconds()))
        delay_payload = {
            "seconds": delay_seconds,
            "calculated_at": _iso(now),
            "latest_at": _iso(latest_ts),
        }
    analytics: dict[str, Any] = {
        "id": str(node_id),
        "range": {
            "start": _iso(start_utc),
            "end": _iso(end_utc),
        },
        "views": {
            "total": views_total,
            "buckets": buckets,
            "last_updated_at": _iso(latest_views_updated),
        },
        "reactions": {
            "totals": reactions_totals,
            "last_reaction_at": _iso(latest_reaction_at),
        },
        "comments": {
            "total": comments_summary["total"],
            "by_status": comments_summary["by_status"],
            "last_created_at": _iso(comments_last_created),
        },
    }
    if delay_payload:
        analytics["delay"] = delay_payload
    return analytics


def _analytics_to_csv(payload: dict[str, Any]) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["bucket_date", "views", "total_likes", "total_comments"])
    totals = payload.get("reactions", {}).get("totals", {})
    total_likes = sum(int(value) for value in totals.values())
    total_comments = int(payload.get("comments", {}).get("total") or 0)
    for bucket in payload.get("views", {}).get("buckets", []):
        writer.writerow(
            [
                bucket.get("bucket_date"),
                bucket.get("views"),
                total_likes,
                total_comments,
            ]
        )
    return buffer.getvalue()


async def _resolve_node_id(node_identifier: str, container, engine: AsyncEngine) -> int:
    try:
        return int(str(node_identifier))
    except (TypeError, ValueError):
        pass
    candidate = str(node_identifier)
    try:
        dto = await container.nodes_service._repo_get_by_slug_async(candidate)
    except (AttributeError, RuntimeError, SQLAlchemyError) as exc:
        logger.debug("nodes_admin_resolve_slug_failed", extra={"slug": candidate}, exc_info=exc)
        dto = None
    if dto is not None and getattr(dto, "id", None) is not None:
        try:
            return int(dto.id)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            logger.debug(
                "nodes_admin_resolve_invalid_id",
                extra={"slug": candidate, "raw_id": getattr(dto, "id", None)},
            )
    try:
        async with engine.begin() as conn:
            resolved = (
                await conn.execute(
                    text("SELECT id FROM nodes WHERE slug = :slug"),
                    {"slug": candidate},
                )
            ).scalar()
    except SQLAlchemyError as exc:
        logger.error("nodes_admin_resolve_query_failed", extra={"slug": candidate}, exc_info=exc)
        raise HTTPException(status_code=500, detail="lookup_failed") from None
    if resolved is None:
        raise HTTPException(status_code=404, detail="not_found")
    return int(resolved)


async def _fetch_moderation_detail(engine: AsyncEngine, node_id: int) -> dict[str, Any] | None:
    async with engine.begin() as conn:
        row = (
            (
                await conn.execute(
                    text(
                        """
                    SELECT id,
                           slug,
                           title,
                           author_id::text AS author_id,
                           status,
                           is_public,
                           created_at,
                           updated_at,
                           moderation_status,
                           moderation_status_updated_at
                    FROM nodes
                    WHERE id = :id
                    """
                    ),
                    {"id": node_id},
                )
            )
            .mappings()
            .first()
        )
        if row is None:
            return None
        history_rows = (
            (
                await conn.execute(
                    text(
                        """
                    SELECT id,
                           action,
                           status,
                           reason,
                           actor_id,
                           decided_at
                    FROM node_moderation_history
                    WHERE node_id = :id
                    ORDER BY decided_at DESC
                    LIMIT 100
                    """
                    ),
                    {"id": node_id},
                )
            )
            .mappings()
            .all()
        )
    return _build_moderation_detail(dict(row), [dict(entry) for entry in history_rows])


def _build_moderation_detail(
    row: dict[str, Any], history_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    moderation_status = _normalize_moderation_status(row.get("moderation_status"))
    history: list[dict[str, Any]] = []
    for entry in history_rows:
        history.append(
            {
                "action": entry.get("action"),
                "status": _normalize_moderation_status(entry.get("status")),
                "reason": entry.get("reason"),
                "actor": entry.get("actor_id"),
                "decided_at": _iso(entry.get("decided_at")),
            }
        )
    meta: dict[str, Any] = {
        "node_status": row.get("status"),
        "moderation_status": moderation_status,
        "moderation_status_updated_at": _iso(row.get("moderation_status_updated_at")),
        "created_at": _iso(row.get("created_at")),
        "updated_at": _iso(row.get("updated_at")),
        "slug": row.get("slug"),
        "is_public": row.get("is_public"),
    }
    return {
        "id": str(row.get("id")),
        "type": "node",
        "author_id": row.get("author_id"),
        "preview": row.get("title"),
        "status": moderation_status,
        "moderation_history": history,
        "meta": meta,
        "reports": [],
    }
