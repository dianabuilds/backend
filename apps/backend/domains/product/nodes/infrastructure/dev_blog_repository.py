from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.product.nodes.utils import iso_datetime, strip_html_summary

DEV_BLOG_TAG = "dev-blog"
_DEFAULT_PREVIEW_STATUSES: tuple[str, ...] = (
    "draft",
    "scheduled",
    "scheduled_unpublish",
    "published",
    "archived",
)
_ORDER_EXPR = "COALESCE(n.publish_at, n.updated_at, n.created_at)"
_PUBLISHED_CONDITION = (
    "n.status = 'published' AND n.is_public = true "
    "AND (n.publish_at IS NULL OR n.publish_at <= now())"
)


class DevBlogRepository:
    async def fetch_page(
        self, engine: AsyncEngine, *, limit: int, offset: int
    ) -> tuple[list[dict[str, Any]], int]:
        params = {"tag": DEV_BLOG_TAG, "limit": int(limit), "offset": int(offset)}
        async with engine.begin() as conn:
            try:
                rows = (
                    (
                        await conn.execute(
                            text(
                                f"""
                                SELECT n.id,
                                       n.slug,
                                       n.title,
                                       n.author_id::text AS author_id,
                                       n.publish_at,
                                       n.updated_at,
                                       n.cover_url,
                                       n.content_html
                                  FROM nodes AS n
                                 WHERE EXISTS (
                                         SELECT 1
                                           FROM product_node_tags AS t
                                          WHERE t.node_id = n.id AND t.slug = :tag
                                     )
                                   AND {_PUBLISHED_CONDITION}
                                 ORDER BY {_ORDER_EXPR} DESC, n.id DESC
                                 LIMIT :limit OFFSET :offset
                                """
                            ),
                            params,
                        )
                    )
                    .mappings()
                    .all()
                )
            except SQLAlchemyError:
                raise
            items = [self._row_to_summary(row) for row in rows]
            try:
                total = await conn.execute(
                    text(
                        f"""
                        SELECT COUNT(*)::bigint
                          FROM nodes AS n
                         WHERE EXISTS (
                                 SELECT 1
                                   FROM product_node_tags AS t
                                  WHERE t.node_id = n.id AND t.slug = :tag
                             )
                           AND {_PUBLISHED_CONDITION}
                        """
                    ),
                    {"tag": DEV_BLOG_TAG},
                )
                total_count = int(total.scalar_one())
            except SQLAlchemyError:
                total_count = offset + len(items)
        return items, total_count

    async def fetch_latest_for_home(
        self, engine: AsyncEngine, *, limit: int
    ) -> list[dict[str, Any]]:
        params = {"tag": DEV_BLOG_TAG, "limit": int(limit)}
        async with engine.begin() as conn:
            try:
                rows = (
                    (
                        await conn.execute(
                            text(
                                f"""
                                SELECT n.id,
                                       n.slug,
                                       n.title,
                                       n.author_id::text AS author_id,
                                       n.publish_at,
                                       n.updated_at,
                                       n.cover_url,
                                       n.content_html
                                  FROM nodes AS n
                                 WHERE EXISTS (
                                         SELECT 1
                                           FROM product_node_tags AS t
                                          WHERE t.node_id = n.id AND t.slug = :tag
                                     )
                                   AND {_PUBLISHED_CONDITION}
                                 ORDER BY {_ORDER_EXPR} DESC, n.id DESC
                                 LIMIT :limit
                                """
                            ),
                            params,
                        )
                    )
                    .mappings()
                    .all()
                )
            except SQLAlchemyError:
                raise
        return [self._row_to_summary(row) for row in rows]

    async def fetch_post_by_slug(
        self,
        engine: AsyncEngine,
        *,
        slug: str,
        include_unpublished: bool = False,
        allowed_statuses: Sequence[str] | None = None,
    ) -> dict[str, Any] | None:
        params: dict[str, Any] = {"slug": slug, "tag": DEV_BLOG_TAG}
        if include_unpublished:
            statuses = tuple(
                dict.fromkeys(allowed_statuses or _DEFAULT_PREVIEW_STATUSES)
            )
            if not statuses:
                statuses = ("published",)
            params["statuses"] = statuses
            status_clause = "n.status = ANY(:statuses) AND n.status <> 'deleted'"
        else:
            status_clause = _PUBLISHED_CONDITION
        query = f"""
            SELECT n.id,
                   n.slug,
                   n.title,
                   n.author_id::text AS author_id,
                   n.publish_at,
                   n.updated_at,
                   n.cover_url,
                   n.content_html,
                   n.status,
                   n.is_public,
                   {_ORDER_EXPR} AS order_value,
                   COALESCE(array_agg(DISTINCT t.slug) FILTER (WHERE t.slug IS NOT NULL), '{{}}') AS tags
              FROM nodes AS n
              LEFT JOIN product_node_tags AS t ON t.node_id = n.id
             WHERE n.slug = :slug
               AND EXISTS (
                       SELECT 1
                         FROM product_node_tags AS tag
                        WHERE tag.node_id = n.id AND tag.slug = :tag
                   )
               AND {status_clause}
             GROUP BY n.id,
                      n.slug,
                      n.title,
                      n.author_id,
                      n.publish_at,
                      n.updated_at,
                      n.created_at,
                      n.cover_url,
                      n.content_html,
                      n.status,
                      n.is_public
        """
        async with engine.begin() as conn:
            try:
                row = (await conn.execute(text(query), params)).mappings().first()
            except SQLAlchemyError:
                raise
        if row is None:
            return None
        detail = self._row_to_detail(row)
        detail["_order_value"] = row.get("order_value")
        return detail

    async def fetch_adjacent(
        self,
        engine: AsyncEngine,
        *,
        sort_value,
        node_id: int,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        params = {
            "tag": DEV_BLOG_TAG,
            "value": sort_value,
            "id": int(node_id),
        }
        prev_sql = text(
            f"""
            SELECT n.id,
                   n.slug,
                   n.title,
                   n.author_id::text AS author_id,
                   n.publish_at,
                   n.updated_at,
                   n.cover_url,
                   n.content_html
              FROM nodes AS n
             WHERE EXISTS (
                     SELECT 1
                       FROM product_node_tags AS t
                      WHERE t.node_id = n.id AND t.slug = :tag
                 )
               AND {_PUBLISHED_CONDITION}
               AND (
                    {_ORDER_EXPR} < :value
                    OR ({_ORDER_EXPR} = :value AND n.id < :id)
               )
             ORDER BY {_ORDER_EXPR} DESC, n.id DESC
             LIMIT 1
            """
        )
        next_sql = text(
            f"""
            SELECT n.id,
                   n.slug,
                   n.title,
                   n.author_id::text AS author_id,
                   n.publish_at,
                   n.updated_at,
                   n.cover_url,
                   n.content_html
              FROM nodes AS n
             WHERE EXISTS (
                     SELECT 1
                       FROM product_node_tags AS t
                      WHERE t.node_id = n.id AND t.slug = :tag
                 )
               AND {_PUBLISHED_CONDITION}
               AND (
                    {_ORDER_EXPR} > :value
                    OR ({_ORDER_EXPR} = :value AND n.id > :id)
               )
             ORDER BY {_ORDER_EXPR} ASC, n.id ASC
             LIMIT 1
            """
        )
        async with engine.begin() as conn:
            try:
                prev_row = (await conn.execute(prev_sql, params)).mappings().first()
                next_row = (await conn.execute(next_sql, params)).mappings().first()
            except SQLAlchemyError:
                raise
        previous = self._row_to_summary(prev_row) if prev_row else None
        next_item = self._row_to_summary(next_row) if next_row else None
        return previous, next_item

    def _row_to_summary(self, row: Any) -> dict[str, Any]:
        if row is None:
            return {}
        raw_id = row.get("id")
        try:
            node_id = int(raw_id) if raw_id is not None else None
        except (TypeError, ValueError):
            node_id = raw_id
        summary = strip_html_summary(row.get("content_html"))
        return {
            "id": node_id,
            "slug": row.get("slug"),
            "title": row.get("title"),
            "summary": summary,
            "cover_url": row.get("cover_url"),
            "publish_at": iso_datetime(row.get("publish_at")),
            "updated_at": iso_datetime(row.get("updated_at")),
            "author": self._author_dict(row.get("author_id")),
        }

    def _row_to_detail(self, row: Any) -> dict[str, Any]:
        data = self._row_to_summary(row)
        data.update(
            {
                "content": row.get("content_html"),
                "status": row.get("status"),
                "is_public": (
                    bool(row.get("is_public"))
                    if row.get("is_public") is not None
                    else None
                ),
                "tags": [str(tag) for tag in row.get("tags") or []],
            }
        )
        return data

    def _author_dict(self, author_id: Any) -> dict[str, Any]:
        if author_id is None:
            return {"id": None}
        return {"id": str(author_id)}
