"""Query helpers for product nodes admin use-cases."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from packages.core.db import get_async_engine  # type: ignore[import-not-found]
from packages.core.sql_fallback import evaluate_sql_backend

from .exceptions import AdminQueryError
from .presenter import (
    _build_moderation_detail,
    _comment_row_to_dict,
    _iso,
    _status_summary_from_counts,
)

logger = logging.getLogger("domains.product.nodes.application.admin_queries")


async def _ensure_engine(container) -> AsyncEngine | None:
    decision = evaluate_sql_backend(getattr(container, "settings", None))
    dsn = decision.dsn
    if not dsn:
        if decision.reason:
            logger.debug("nodes_admin_engine_disabled: %s", decision.reason)
        return None
    if "?" in dsn:
        dsn = dsn.split("?", 1)[0]
    try:
        return get_async_engine("nodes-admin", url=dsn, future=True)
    except SQLAlchemyError as exc:
        logger.error("nodes_admin_engine_init_failed", exc_info=exc)
        return None


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
        raise AdminQueryError(400, f"{field}_invalid") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


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


async def _fetch_engagement_summary(
    engine: AsyncEngine, node_id: int
) -> dict[str, Any]:
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
        row = (
            (await conn.execute(summary_sql, {"node_id": int(node_id)}))
            .mappings()
            .first()
        )
    if row is None:
        raise AdminQueryError(404, "not_found")
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
    comments_summary["last_comment_created_at"] = _iso(
        row.get("last_comment_created_at")
    )
    comments_summary["last_comment_updated_at"] = _iso(
        row.get("last_comment_updated_at")
    )
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
        status_clause = _build_status_condition(
            alias, statuses, params, prefix="status"
        )
        if status_clause:
            conditions.append(status_clause)
        view_mode = view.lower()
        if view_mode == "roots":
            conditions.append(f"{alias}.parent_comment_id IS NULL")
        elif view_mode == "children":
            if parent_id is None:
                raise AdminQueryError(400, "parent_id_required")
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
                raise AdminQueryError(404, "comment_not_found")
            conditions.append(f"{alias}.parent_comment_id = :parent_id")
            params["parent_id"] = int(parent_id)
        elif view_mode == "all":
            pass
        else:
            raise AdminQueryError(400, "view_invalid")
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
            raise AdminQueryError(404, "comment_not_found")
        params: dict[str, Any] = {"root_id": int(root_id), "node_id": int(node_id)}
        conditions: list[str] = ["1=1"]
        status_clause = _build_status_condition(
            alias, statuses, params, prefix="thread_status"
        )
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
            raise AdminQueryError(400, "thread_id_required")
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
        reactions_rows = (
            (await conn.execute(reactions_sql, reactions_params)).mappings().all()
        )
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
        comments_rows = (
            (await conn.execute(comments_sql, comments_params)).mappings().all()
        )
    comments_counts = {row["status"]: int(row["count"] or 0) for row in comments_rows}
    comments_summary = _status_summary_from_counts(comments_counts)
    comments_last_created: datetime | None = None
    if comments_rows:
        comments_last_created = max(
            row["last_created_at"]
            for row in comments_rows
            if row["last_created_at"] is not None
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


async def _resolve_node_id(node_identifier: str, container, engine: AsyncEngine) -> int:
    try:
        return int(str(node_identifier))
    except (TypeError, ValueError):
        pass
    candidate = str(node_identifier)
    try:
        dto = await container.nodes_service._repo_get_by_slug_async(candidate)
    except (AttributeError, RuntimeError, SQLAlchemyError) as exc:
        logger.debug(
            "nodes_admin_resolve_slug_failed", extra={"slug": candidate}, exc_info=exc
        )
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
        logger.error(
            "nodes_admin_resolve_query_failed", extra={"slug": candidate}, exc_info=exc
        )
        raise AdminQueryError(500, "lookup_failed") from None
    if resolved is None:
        raise AdminQueryError(404, "not_found")
    return int(resolved)


async def _fetch_moderation_detail(
    engine: AsyncEngine, node_id: int
) -> dict[str, Any] | None:
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


__all__ = [
    "_append_comment_filters",
    "_build_status_condition",
    "_ensure_engine",
    "_ensure_utc",
    "_fetch_analytics",
    "_fetch_comment_collection",
    "_fetch_comment_thread",
    "_fetch_comments_data",
    "_fetch_engagement_summary",
    "_fetch_moderation_detail",
    "_parse_query_datetime",
    "_resolve_node_id",
]
