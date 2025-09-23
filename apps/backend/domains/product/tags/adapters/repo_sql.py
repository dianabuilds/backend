from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from domains.product.tags.application.ports import Repo
from domains.product.tags.domain.results import TagView


class SQLTagsRepo(Repo):
    """Read-only tags repo backed by aggregated usage counters.

    Expects table `tag_usage_counters(author_id uuid, content_type text, slug text, count int)`
    and optional `tag(slug text, name text, ...)` for naming.
    """

    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            create_async_engine(str(engine)) if isinstance(engine, str) else engine
        )

    def _build_query(self, popular: bool) -> str:
        order = "u.count DESC, name ASC" if popular else "name ASC, u.slug ASC"
        base = """
            SELECT u.slug AS slug,
                   COALESCE(t.name, u.slug) AS name,
                   u.count::int AS count
            FROM (
              SELECT slug, SUM(count) AS count
              FROM tag_usage_counters
              WHERE author_id = :uid
                AND (:ctype IS NULL OR content_type = :ctype)
              GROUP BY slug
            ) AS u
            LEFT JOIN tag AS t ON t.slug = u.slug
            WHERE (:q IS NULL
                   OR u.slug ILIKE '%' || :q || '%'
                   OR COALESCE(t.name, '') ILIKE '%' || :q || '%')
            ORDER BY
            """
        return base + order + "\n            LIMIT :limit OFFSET :offset\n            "

    def list_for_user(
        self,
        user_id: str,
        q: str | None,
        popular: bool,
        limit: int,
        offset: int,
        content_type: str | None = None,
    ) -> list[TagView]:
        # Synchronous API expected by ports; run query synchronously via async engine .run_sync
        # but we can instead use asyncio loop. To keep a simple interface, use run_until_complete pattern
        import asyncio

        async def _run() -> list[TagView]:
            sql = text(self._build_query(popular))
            params: dict[str, Any] = {
                "uid": user_id,
                "q": q,
                "ctype": content_type,
                "limit": int(limit),
                "offset": int(offset),
            }
            async with self._engine.begin() as conn:
                rows = (await conn.execute(sql, params)).mappings().all()
                return [
                    TagView(slug=str(r["slug"]), name=str(r["name"]), count=int(r["count"]))
                    for r in rows
                ]

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]


__all__ = ["SQLTagsRepo"]
