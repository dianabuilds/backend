from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from apps.backend.app.api_gateway.routers import get_container
from domains.platform.iam.security import get_current_user
from domains.product.navigation.api.support import DEV_BLOG_TAG
from domains.product.navigation.infrastructure import ensure_engine

logger = logging.getLogger(__name__)


def register_relations_routes(router: APIRouter) -> None:
    """Attach public navigation relations endpoints."""

    @router.get("/related/{node_id}")
    async def related_nodes(
        node_id: int,
        limit: int = Query(ge=1, le=50, default=6),
        algo: str = Query(default="tags"),
        container=Depends(get_container),
        claims=Depends(get_current_user),
    ):
        eng = await ensure_engine(container)
        if eng is None:
            return []

        async with eng.connect() as _conn:
            cur = (
                (
                    await _conn.execute(
                        text(
                            "SELECT author_id::text AS author_id, is_public,"
                            "       EXISTS (SELECT 1 FROM product_node_tags WHERE node_id = :id AND slug = :dev_tag) AS is_dev_blog"
                            " FROM nodes WHERE id = :id"
                        ),
                        {"id": int(node_id), "dev_tag": DEV_BLOG_TAG},
                    )
                )
                .mappings()
                .first()
            )
            if _conn.in_transaction():
                await _conn.rollback()
        if not cur:
            raise HTTPException(status_code=404, detail="not_found")
        if bool(cur.get("is_dev_blog")):
            return []
        uid = str(claims.get("sub") or "") if claims else ""
        role = str(claims.get("role") or "").lower()
        allow_private = bool(
            uid and (uid == str(cur.get("author_id") or "") or role == "admin")
        )
        algo = (algo or "tags").lower()

        async def _load_tags(conn, lim: int) -> list[dict]:
            sql = text(
                """
                WITH cur_tags AS (
                  SELECT slug FROM product_node_tags WHERE node_id = :nid AND slug <> :dev_tag
                )
                SELECT n.id,
                       n.slug,
                       n.title,
                       n.cover_url,
                       n.is_public,
                       COUNT(*)::float AS score
                FROM product_node_tags t
                JOIN cur_tags ct ON ct.slug = t.slug
                JOIN nodes n ON n.id = t.node_id
                WHERE t.node_id <> :nid
                  AND (:allow OR n.is_public = true)
                  AND NOT EXISTS (SELECT 1 FROM product_node_tags AS dt WHERE dt.node_id = n.id AND dt.slug = :dev_tag)
                GROUP BY n.id, n.slug, n.title, n.cover_url, n.is_public
                ORDER BY score DESC, n.updated_at DESC, n.id DESC
                LIMIT :lim
                """
            )
            try:
                rows = (
                    (
                        await conn.execute(
                            sql,
                            {
                                "nid": int(node_id),
                                "lim": int(lim),
                                "allow": bool(allow_private),
                                "dev_tag": DEV_BLOG_TAG,
                            },
                        )
                    )
                    .mappings()
                    .all()
                )
                return [
                    {
                        "id": int(r["id"]),
                        "slug": r.get("slug"),
                        "title": r.get("title"),
                        "cover_url": r.get("cover_url"),
                        "is_public": bool(r.get("is_public", False)),
                        "score": float(r.get("score") or 0.0),
                        "reason": "tags",
                    }
                    for r in rows
                ]
            except SQLAlchemyError:
                logger.debug(
                    "navigation related: tags query fallback triggered", exc_info=True
                )
                try:
                    if conn.in_transaction():
                        await conn.rollback()
                except SQLAlchemyError:
                    pass
                sql2 = text(
                    """
                    WITH cur_tags AS (
                      SELECT slug FROM product_node_tags WHERE node_id = :nid AND slug <> :dev_tag
                    )
                    SELECT n.id,
                           n.title,
                           n.is_public,
                           COUNT(*)::float AS score
                    FROM product_node_tags t
                    JOIN cur_tags ct ON ct.slug = t.slug
                    JOIN nodes n ON n.id = t.node_id
                    WHERE t.node_id <> :nid
                      AND (:allow OR n.is_public = true)
                      AND NOT EXISTS (SELECT 1 FROM product_node_tags AS dt WHERE dt.node_id = n.id AND dt.slug = :dev_tag)
                    GROUP BY n.id, n.title, n.is_public
                    ORDER BY score DESC, n.updated_at DESC, n.id DESC
                    LIMIT :lim
                    """
                )
                rows = (
                    (
                        await conn.execute(
                            sql2,
                            {
                                "nid": int(node_id),
                                "lim": int(lim),
                                "allow": bool(allow_private),
                                "dev_tag": DEV_BLOG_TAG,
                            },
                        )
                    )
                    .mappings()
                    .all()
                )
                return [
                    {
                        "id": int(r["id"]),
                        "slug": None,
                        "title": r.get("title"),
                        "cover_url": None,
                        "is_public": bool(r.get("is_public", False)),
                        "score": float(r.get("score") or 0.0),
                        "reason": "tags",
                    }
                    for r in rows
                ]

        async def _load_fts(conn, lim: int, title: str | None) -> list[dict]:
            query_title = title or ""
            sql = text(
                """
                SELECT n.id,
                       n.slug,
                       n.title,
                       n.cover_url,
                       n.is_public,
                       ts_rank_cd(n.search_vector, plainto_tsquery('simple', :title)) AS score
                FROM nodes n
                WHERE n.id <> :nid
                  AND (:allow OR n.is_public = true)
                  AND NOT EXISTS (SELECT 1 FROM product_node_tags AS dt WHERE dt.node_id = n.id AND dt.slug = :dev_tag)
                ORDER BY score DESC, n.updated_at DESC, n.id DESC
                LIMIT :lim
                """
            )
            rows = (
                (
                    await conn.execute(
                        sql,
                        {
                            "nid": int(node_id),
                            "lim": int(lim),
                            "allow": bool(allow_private),
                            "dev_tag": DEV_BLOG_TAG,
                            "title": query_title,
                        },
                    )
                )
                .mappings()
                .all()
            )
            return [
                {
                    "id": int(r["id"]),
                    "slug": r.get("slug"),
                    "title": r.get("title"),
                    "cover_url": r.get("cover_url"),
                    "is_public": bool(r.get("is_public", False)),
                    "score": float(r.get("score") or 0.0),
                    "reason": "fts",
                }
                for r in rows
            ]

        async def _load_node_title(conn) -> str | None:
            sql = text("SELECT title FROM nodes WHERE id = :nid")
            row = (
                (
                    await conn.execute(
                        sql,
                        {
                            "nid": int(node_id),
                        },
                    )
                )
                .mappings()
                .first()
            )
            return row.get("title") if row else None

        async def _get_cached(conn, algo_key: str, lim: int) -> list[dict]:
            ttl_sec = int(
                getattr(container.settings, "nav_related_ttl", 21_600) or 21_600
            )
            cutoff = datetime.now(UTC) - timedelta(seconds=ttl_sec)
            try:
                async with eng.begin() as c2:
                    rows = (
                        (
                            await c2.execute(
                                text(
                                    "SELECT c.target_id AS id, c.score, n.slug, n.title, n.cover_url, n.is_public \n"
                                    "FROM node_assoc_cache c JOIN nodes n ON n.id = c.target_id \n"
                                    "WHERE c.source_id = :sid AND c.algo = :algo AND c.updated_at >= :cut \n"
                                    "AND (:allow OR n.is_public = true) \n"
                                    "ORDER BY c.score DESC, n.updated_at DESC, n.id DESC LIMIT :lim"
                                ),
                                {
                                    "sid": int(node_id),
                                    "algo": algo_key,
                                    "cut": cutoff,
                                    "allow": bool(allow_private),
                                    "lim": int(lim),
                                    "dev_tag": DEV_BLOG_TAG,
                                },
                            )
                        )
                        .mappings()
                        .all()
                    )
            except SQLAlchemyError:
                return []
            return [
                {
                    "id": int(r["id"]),
                    "slug": r.get("slug"),
                    "title": r.get("title"),
                    "cover_url": r.get("cover_url"),
                    "is_public": bool(r.get("is_public", False)),
                    "score": float(r.get("score") or 0.0),
                    "reason": algo_key,
                }
                for r in rows
            ]

        async def _store_cache(conn, algo_key: str, items: list[dict]) -> None:
            if not items:
                return
            try:
                async with eng.begin() as c2:
                    for it in items:
                        await c2.execute(
                            text(
                                "INSERT INTO node_assoc_cache(source_id, target_id, algo, score, updated_at) \n"
                                "VALUES (:sid, :tid, :algo, :score, now()) \n"
                                "ON CONFLICT (source_id, target_id, algo) DO UPDATE SET score = EXCLUDED.score, updated_at = now()"
                            ),
                            {
                                "sid": int(node_id),
                                "tid": int(it["id"]),
                                "algo": algo_key,
                                "score": float(it.get("score") or 0.0),
                            },
                        )
            except SQLAlchemyError:
                return

        async with eng.connect() as conn:
            if algo in ("tags", "auto"):
                cached = await _get_cached(conn, "tags", limit)
                if cached:
                    return cached
                res = await _load_tags(conn, limit)
                await _store_cache(conn, "tags", res)
                return res
            elif algo == "fts" or algo == "embedding":
                cached = await _get_cached(conn, "fts", limit)
                if cached:
                    return cached
                title = await _load_node_title(conn)
                res = await _load_fts(conn, limit, title)
                await _store_cache(conn, "fts", res)
                return res
            elif algo == "mix" or algo == "explore":
                tags_cached = await _get_cached(conn, "tags", limit)
                fts_cached = await _get_cached(conn, "fts", limit)
                if not fts_cached:
                    title = await _load_node_title(conn)
                    fts_cached = await _load_fts(conn, limit, title)
                    await _store_cache(conn, "fts", fts_cached)
                if not tags_cached:
                    tags_cached = await _load_tags(conn, limit)
                    await _store_cache(conn, "tags", tags_cached)
                seen: set[int] = set()
                merged: list[dict] = []
                streams = [tags_cached, fts_cached]
                idx = 0
                while len(merged) < limit and any(streams):
                    cur_stream = streams[idx % 2]
                    if cur_stream:
                        item = cur_stream.pop(0)
                        if int(item["id"]) not in seen:
                            seen.add(int(item["id"]))
                            merged.append(item)
                    idx += 1
                return merged
            else:
                res = await _load_tags(conn, limit)
                await _store_cache(conn, "tags", res)
                return res
