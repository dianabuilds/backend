from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.product.nodes.utils import iso_datetime, strip_html_summary

DEV_BLOG_TAG = "dev-blog"


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
                                """
                                SELECT n.id,
                                       n.slug,
                                       n.title,
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
                                   AND n.status = 'published'
                                   AND n.is_public = true
                                   AND (n.publish_at IS NULL OR n.publish_at <= now())
                                 ORDER BY COALESCE(n.publish_at, n.updated_at, n.created_at) DESC, n.id DESC
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
            items: list[dict[str, Any]] = []
            for row in rows:
                row_id = row.get("id")
                try:
                    node_id = int(row_id) if row_id is not None else None
                except (TypeError, ValueError):
                    node_id = row_id
                publish_at = row.get("publish_at")
                updated_at = row.get("updated_at")
                items.append(
                    {
                        "id": node_id,
                        "slug": row.get("slug"),
                        "title": row.get("title"),
                        "cover_url": row.get("cover_url"),
                        "publish_at": iso_datetime(publish_at),
                        "updated_at": iso_datetime(updated_at),
                        "summary": strip_html_summary(row.get("content_html")),
                    }
                )
            try:
                total = await conn.execute(
                    text(
                        """
                        SELECT COUNT(*)::bigint
                          FROM nodes AS n
                         WHERE EXISTS (
                                 SELECT 1
                                   FROM product_node_tags AS t
                                  WHERE t.node_id = n.id AND t.slug = :tag
                             )
                           AND n.status = 'published'
                           AND n.is_public = true
                           AND (n.publish_at IS NULL OR n.publish_at <= now())
                        """
                    ),
                    {"tag": DEV_BLOG_TAG},
                )
                total_count = int(total.scalar_one())
            except SQLAlchemyError:
                total_count = offset + len(items)
        return items, total_count
