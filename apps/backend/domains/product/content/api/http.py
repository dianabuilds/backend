from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from apps.backend import get_container
from packages.core.config import to_async_dsn

logger = logging.getLogger(__name__)


def _iso(dt: Any) -> str | None:
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")
    try:
        return _iso(datetime.fromisoformat(str(dt)))
    except Exception:
        return None


async def _ensure_engine(settings) -> AsyncEngine | None:
    try:
        dsn = to_async_dsn(settings.database_url)
        if not dsn:
            return None
        if "?" in dsn:
            dsn = dsn.split("?", 1)[0]
        return create_async_engine(dsn, future=True)
    except Exception:
        logger.exception("content analytics: failed to create engine")
        return None


async def _fetch_stats(engine: AsyncEngine) -> dict[str, Any]:
    defaults = {
        "nodes": 0,
        "quests": 0,
        "worlds": 0,
        "published": 0,
        "drafts": 0,
        "linksPerObject": 0.0,
    }
    try:
        async with engine.begin() as conn:
            node_row = (
                (
                    await conn.execute(
                        text(
                            "SELECT COUNT(*)::bigint AS total,\n"
                            "       SUM(CASE WHEN status = 'published' THEN 1 ELSE 0 END)::bigint AS published,\n"
                            "       SUM(CASE WHEN status IN ('draft','scheduled','scheduled_unpublish') THEN 1 ELSE 0 END)::bigint AS drafts\n"
                            "FROM nodes"
                        )
                    )
                )
                .mappings()
                .first()
            )
            quest_row = (
                (await conn.execute(text("SELECT COUNT(*)::bigint AS total FROM quests")))
                .mappings()
                .first()
            )
            world_row = (
                (await conn.execute(text("SELECT COUNT(*)::bigint AS total FROM worlds")))
                .mappings()
                .first()
            )
            links_row = (
                (
                    await conn.execute(
                        text(
                            "SELECT COUNT(*)::bigint AS links, COUNT(DISTINCT source_id)::bigint AS sources FROM node_assoc_cache"
                        )
                    )
                )
                .mappings()
                .first()
            )
    except Exception:
        logger.exception("content analytics: stats query failed")
        return defaults
    total_nodes = int(node_row.get("total", 0)) if node_row else 0
    published = int(node_row.get("published", 0)) if node_row else 0
    drafts = int(node_row.get("drafts", 0)) if node_row else 0
    quests = int(quest_row.get("total", 0)) if quest_row else 0
    worlds = int(world_row.get("total", 0)) if world_row else 0
    links = int(links_row.get("links", 0)) if links_row else 0
    sources = int(links_row.get("sources", 0)) if links_row else 0
    links_per_object = float(links) / float(sources) if sources else 0.0
    return {
        "nodes": total_nodes,
        "quests": quests,
        "worlds": worlds,
        "published": published,
        "drafts": drafts,
        "linksPerObject": round(links_per_object, 2),
    }


async def _fetch_top_tags(engine: AsyncEngine, limit: int) -> list[dict[str, Any]]:
    try:
        async with engine.begin() as conn:
            rows = (
                (
                    await conn.execute(
                        text(
                            "SELECT COALESCE(t.slug, u.slug) AS slug, COALESCE(t.name, u.slug) AS name,\n"
                            "       SUM(u.count)::bigint AS usage_count\n"
                            "  FROM tag_usage_counters u\n"
                            "  LEFT JOIN tag t ON t.slug = u.slug\n"
                            " GROUP BY COALESCE(t.slug, u.slug), COALESCE(t.name, u.slug)\n"
                            " ORDER BY usage_count DESC\n"
                            " LIMIT :lim"
                        ),
                        {"lim": int(limit)},
                    )
                )
                .mappings()
                .all()
            )
    except Exception:
        logger.exception("content analytics: top tags query failed")
        return []
    return [
        {
            "slug": row.get("slug"),
            "name": row.get("name"),
            "count": int(row.get("usage_count", 0)),
            "trend": 0.0,
        }
        for row in rows
    ]


async def _fetch_recent_nodes(engine: AsyncEngine, limit: int) -> list[dict[str, Any]]:
    try:
        async with engine.begin() as conn:
            rows = (
                (
                    await conn.execute(
                        text(
                            "SELECT id, title, author_id::text AS author_id, updated_at\n"
                            "  FROM nodes\n"
                            " ORDER BY updated_at DESC NULLS LAST, id DESC\n"
                            " LIMIT :lim"
                        ),
                        {"lim": int(limit)},
                    )
                )
                .mappings()
                .all()
            )
    except Exception:
        logger.exception("content analytics: recent nodes query failed")
        return []
    return [
        {
            "id": int(row.get("id")),
            "title": row.get("title"),
            "author_id": row.get("author_id"),
            "updated_at": row.get("updated_at"),
        }
        for row in rows
    ]


async def _fetch_recent_quests(engine: AsyncEngine, limit: int) -> list[dict[str, Any]]:
    try:
        async with engine.begin() as conn:
            rows = (
                (
                    await conn.execute(
                        text(
                            "SELECT id::text AS id, title, author_id::text AS author_id, updated_at, is_public\n"
                            "  FROM quests\n"
                            " WHERE is_public = false\n"
                            " ORDER BY updated_at DESC NULLS LAST, id DESC\n"
                            " LIMIT :lim"
                        ),
                        {"lim": int(limit)},
                    )
                )
                .mappings()
                .all()
            )
    except Exception:
        logger.exception("content analytics: recent quests query failed")
        return []
    return [
        {
            "id": row.get("id"),
            "title": row.get("title"),
            "author_id": row.get("author_id"),
            "updated_at": row.get("updated_at"),
        }
        for row in rows
    ]


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/content", tags=["content-analytics"])

    @router.get("/stats")
    async def content_stats(container=Depends(get_container)):
        engine = await _ensure_engine(container.settings)
        if engine is None:
            raise HTTPException(status_code=503, detail="storage_unavailable")
        return await _fetch_stats(engine)

    @router.get("/tags/top")
    async def top_tags(
        limit: int = Query(default=5, ge=1, le=50),
        container=Depends(get_container),
    ):
        engine = await _ensure_engine(container.settings)
        if engine is None:
            return {"items": []}
        items = await _fetch_top_tags(engine, limit)
        return {"items": items}

    @router.get("/edits")
    async def recent_edits(
        limit: int = Query(default=10, ge=1, le=100),
        container=Depends(get_container),
    ):
        engine = await _ensure_engine(container.settings)
        if engine is None:
            return {"items": []}
        nodes = await _fetch_recent_nodes(engine, limit)
        items: list[dict[str, Any]] = []
        for row in nodes:
            items.append(
                {
                    "id": row.get("id"),
                    "user": {"id": row.get("author_id")},
                    "action": f"updated node '{row.get('title') or ''}'",
                    "when": _iso(row.get("updated_at")),
                }
            )
        return {"items": items}

    @router.get("/drafts")
    async def draft_items(
        limit: int = Query(default=50, ge=1, le=200),
        container=Depends(get_container),
    ):
        engine = await _ensure_engine(container.settings)
        if engine is None:
            return {"items": []}
        node_rows = await _fetch_recent_nodes(engine, limit)
        quest_rows = await _fetch_recent_quests(engine, limit)
        combined: list[dict[str, Any]] = []
        for row in node_rows:
            combined.append(
                {
                    "id": str(row.get("id")),
                    "type": "node",
                    "title": row.get("title"),
                    "world": "-",
                    "updatedAt": _iso(row.get("updated_at")),
                }
            )
        for row in quest_rows:
            combined.append(
                {
                    "id": row.get("id"),
                    "type": "quest",
                    "title": row.get("title"),
                    "world": "-",
                    "updatedAt": _iso(row.get("updated_at")),
                }
            )
        combined.sort(key=lambda item: item.get("updatedAt") or "", reverse=True)
        return {"items": combined[:limit]}

    return router


__all__ = ["make_router"]
