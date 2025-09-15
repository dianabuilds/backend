from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from domains.product.tags.application.admin_ports import AdminRepo
from domains.product.tags.domain.admin_models import (
    AliasView,
    BlacklistItem,
    TagListItem,
)


class SQLAdminRepo(AdminRepo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            create_async_engine(str(engine)) if isinstance(engine, str) else engine
        )

    async def _exists_tag(self, tag_id: str) -> bool:
        sql = text("SELECT 1 FROM product_tag WHERE id = :id")
        async with self._engine.begin() as conn:
            row = (await conn.execute(sql, {"id": tag_id})).first()
            return bool(row)

    def list_with_counters(
        self, q: str | None, limit: int, offset: int, content_type: str | None = None
    ) -> list[TagListItem]:
        import asyncio

        async def _run() -> list[TagListItem]:
            sql = text(
                """
                WITH usage AS (
                  SELECT slug, SUM(count)::int AS usage_count
                  FROM product_tag_usage_counters
                  WHERE (:ctype IS NULL OR content_type = :ctype)
                  GROUP BY slug
                ), alia AS (
                  SELECT tag_id, COUNT(*)::int AS aliases_count
                  FROM product_tag_alias
                  GROUP BY tag_id
                )
                SELECT t.id, t.slug, t.name, t.created_at, t.is_hidden,
                       COALESCE(u.usage_count, 0) AS usage_count,
                       COALESCE(a.aliases_count, 0) AS aliases_count
                FROM product_tag t
                LEFT JOIN usage u ON u.slug = t.slug
                LEFT JOIN alia a ON a.tag_id = t.id
                WHERE (:q IS NULL OR t.slug ILIKE '%' || :q || '%' OR t.name ILIKE '%' || :q || '%')
                ORDER BY t.name ASC, t.slug ASC
                LIMIT :limit OFFSET :offset
                """
            )
            params = {
                "q": q,
                "limit": int(limit),
                "offset": int(offset),
                "ctype": content_type,
            }
            async with self._engine.begin() as conn:
                rows = (await conn.execute(sql, params)).mappings().all()
                return [
                    TagListItem(
                        id=str(r["id"]),
                        slug=str(r["slug"]),
                        name=str(r["name"]),
                        created_at=r["created_at"],
                        is_hidden=bool(r["is_hidden"]),
                        usage_count=int(r["usage_count"]),
                        aliases_count=int(r["aliases_count"]),
                    )
                    for r in rows
                ]

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]

    def list_aliases(self, tag_id: str) -> list[AliasView]:
        import asyncio

        async def _run() -> list[AliasView]:
            sql = text(
                "SELECT id, tag_id, alias, type, created_at FROM product_tag_alias WHERE tag_id = :tid ORDER BY created_at DESC"
            )
            async with self._engine.begin() as conn:
                rows = (await conn.execute(sql, {"tid": tag_id})).mappings().all()
                return [
                    AliasView(
                        id=str(r["id"]),
                        tag_id=str(r["tag_id"]),
                        alias=str(r["alias"]),
                        type=str(r["type"]),
                        created_at=r["created_at"],
                    )
                    for r in rows
                ]

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]

    def add_alias(self, tag_id: str, alias: str) -> AliasView:
        import asyncio

        async def _run() -> AliasView:
            if not await self._exists_tag(tag_id):
                raise ValueError("tag_not_found")
            sql = text(
                """
                INSERT INTO product_tag_alias(tag_id, alias, type)
                VALUES (:tid, :alias, 'alias')
                RETURNING id, tag_id, alias, type, created_at
                """
            )
            async with self._engine.begin() as conn:
                try:
                    r = (
                        (await conn.execute(sql, {"tid": tag_id, "alias": alias}))
                        .mappings()
                        .first()
                    )
                except Exception as e:  # unique violation
                    raise ValueError("alias_conflict") from e
                assert r is not None
                return AliasView(
                    id=str(r["id"]),
                    tag_id=str(r["tag_id"]),
                    alias=str(r["alias"]),
                    type=str(r["type"]),
                    created_at=r["created_at"],
                )

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]

    def remove_alias(self, alias_id: str) -> None:
        import asyncio

        async def _run() -> None:
            sql = text("DELETE FROM product_tag_alias WHERE id = :id")
            async with self._engine.begin() as conn:
                await conn.execute(sql, {"id": alias_id})

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(_run())
        else:
            loop.run_until_complete(_run())  # type: ignore[misc]

    def blacklist_list(self, q: str | None) -> list[BlacklistItem]:
        import asyncio

        async def _run() -> list[BlacklistItem]:
            base = "SELECT slug, reason, created_at FROM product_tag_blacklist"
            if q:
                sql = text(
                    base + " WHERE slug ILIKE '%' || :q || '%' ORDER BY created_at DESC"
                )
                params = {"q": q}
            else:
                sql = text(base + " ORDER BY created_at DESC")
                params = {}
            async with self._engine.begin() as conn:
                rows = (await conn.execute(sql, params)).mappings().all()
                return [
                    BlacklistItem(
                        slug=str(r["slug"]),
                        reason=r["reason"],
                        created_at=r["created_at"],
                    )
                    for r in rows
                ]

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]

    def blacklist_add(self, slug: str, reason: str | None) -> BlacklistItem:
        import asyncio

        async def _run() -> BlacklistItem:
            sql = text(
                """
                INSERT INTO product_tag_blacklist(slug, reason)
                VALUES (:slug, :reason)
                ON CONFLICT (slug) DO UPDATE SET reason = EXCLUDED.reason
                RETURNING slug, reason, created_at
                """
            )
            async with self._engine.begin() as conn:
                r = (
                    (await conn.execute(sql, {"slug": slug, "reason": reason}))
                    .mappings()
                    .first()
                )
                assert r is not None
                return BlacklistItem(
                    slug=str(r["slug"]), reason=r["reason"], created_at=r["created_at"]
                )

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]

    def blacklist_delete(self, slug: str) -> None:
        import asyncio

        async def _run() -> None:
            sql = text("DELETE FROM product_tag_blacklist WHERE slug = :slug")
            async with self._engine.begin() as conn:
                await conn.execute(sql, {"slug": slug})

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(_run())
        else:
            loop.run_until_complete(_run())  # type: ignore[misc]

    def create_tag(self, slug: str, name: str) -> TagListItem:
        import asyncio

        async def _run() -> TagListItem:
            sql = text(
                """
                INSERT INTO product_tag(slug, name) VALUES (:slug, :name)
                ON CONFLICT (slug) DO NOTHING
                RETURNING id, slug, name, created_at, is_hidden
                """
            )
            async with self._engine.begin() as conn:
                r = (
                    (await conn.execute(sql, {"slug": slug, "name": name}))
                    .mappings()
                    .first()
                )
                if r is None:
                    # slug conflict
                    raise ValueError("conflict")
                # compute usage count
                sql2 = text(
                    "SELECT COALESCE(SUM(count),0)::int AS c FROM product_tag_usage_counters WHERE slug = :slug"
                )
                usage_row = (
                    (await conn.execute(sql2, {"slug": slug})).mappings().first()
                )
                usage = int(usage_row["c"]) if usage_row else 0
                return TagListItem(
                    id=str(r["id"]),
                    slug=str(r["slug"]),
                    name=str(r["name"]),
                    created_at=r["created_at"],
                    is_hidden=bool(r["is_hidden"]),
                    usage_count=int(usage),
                    aliases_count=0,
                )

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]

    def delete_tag(self, tag_id: str) -> None:
        import asyncio

        async def _run() -> None:
            # Capture slug then delete tag and related data
            async with self._engine.begin() as conn:
                r = (
                    (
                        await conn.execute(
                            text("SELECT slug FROM product_tag WHERE id = :id"),
                            {"id": tag_id},
                        )
                    )
                    .mappings()
                    .first()
                )
                if not r:
                    return
                slug = str(r["slug"])
                await conn.execute(
                    text("DELETE FROM product_tag WHERE id = :id"), {"id": tag_id}
                )
                await conn.execute(
                    text("DELETE FROM product_tag_usage_counters WHERE slug = :slug"),
                    {"slug": slug},
                )

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(_run())
        else:
            loop.run_until_complete(_run())  # type: ignore[misc]

    def merge_dry_run(
        self, from_id: str, to_id: str, content_type: str | None = None
    ) -> dict:
        import asyncio

        async def _run() -> dict:
            sql = text("SELECT id, slug, name FROM product_tag WHERE id = :id")
            async with self._engine.begin() as conn:
                f = (await conn.execute(sql, {"id": from_id})).mappings().first()
                t = (await conn.execute(sql, {"id": to_id})).mappings().first()
                if not f or not t:
                    return {"errors": ["tag not found"], "warnings": []}
                cnt_sql = text(
                    "SELECT COALESCE(SUM(count),0)::int AS c FROM product_tag_usage_counters WHERE slug = :slug AND (:ctype IS NULL OR content_type = :ctype)"
                )
                usage_row = (
                    (
                        await conn.execute(
                            cnt_sql, {"slug": f["slug"], "ctype": content_type}
                        )
                    )
                    .mappings()
                    .first()
                )
                aliases_row = (
                    (
                        await conn.execute(
                            text(
                                "SELECT COUNT(*)::int AS n FROM product_tag_alias WHERE tag_id = :tid"
                            ),
                            {"tid": from_id},
                        )
                    )
                    .mappings()
                    .first()
                )
                usage = int(usage_row["c"]) if usage_row else 0
                aliases = int(aliases_row["n"]) if aliases_row else 0
                return {
                    "from": {
                        "id": str(f["id"]),
                        "name": str(f["name"]),
                        "slug": str(f["slug"]),
                    },
                    "to": {
                        "id": str(t["id"]),
                        "name": str(t["name"]),
                        "slug": str(t["slug"]),
                    },
                    "content_touched": 0,
                    "usage_counters": usage,
                    "aliases_moved": aliases,
                    "warnings": [],
                    "errors": [],
                }

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]

    def merge_apply(
        self,
        from_id: str,
        to_id: str,
        actor_id: str | None,
        reason: str | None,
        content_type: str | None = None,
    ) -> dict:
        import asyncio

        async def _run() -> dict:
            report = self.merge_dry_run(from_id, to_id, content_type)
            if report.get("errors"):
                return report
            async with self._engine.begin() as conn:
                # Re-fetch slugs for safety
                sel = text("SELECT id, slug FROM product_tag WHERE id = :id")
                f = (await conn.execute(sel, {"id": from_id})).mappings().first()
                t = (await conn.execute(sel, {"id": to_id})).mappings().first()
                if not f or not t:
                    return report
                fslug = str(f["slug"])
                tslug = str(t["slug"])
                # Move aliases
                await conn.execute(
                    text(
                        "UPDATE product_tag_alias SET tag_id = :tid WHERE tag_id = :fid"
                    ),
                    {"tid": to_id, "fid": from_id},
                )
                # Merge usage counters
                if content_type is None:
                    # merge across all content types
                    await conn.execute(
                        text(
                            """
                            INSERT INTO product_tag_usage_counters(author_id, content_type, slug, count)
                            SELECT author_id, content_type, :tslug AS slug, SUM(count) AS count
                            FROM product_tag_usage_counters
                            WHERE slug IN (:fslug, :tslug)
                            GROUP BY author_id, content_type
                            ON CONFLICT (author_id, content_type, slug) DO UPDATE SET count = EXCLUDED.count
                            """
                        ),
                        {"fslug": fslug, "tslug": tslug},
                    )
                else:
                    await conn.execute(
                        text(
                            """
                            INSERT INTO product_tag_usage_counters(author_id, content_type, slug, count)
                            SELECT author_id, content_type, :tslug AS slug, SUM(count) AS count
                            FROM product_tag_usage_counters
                            WHERE slug IN (:fslug, :tslug) AND content_type = :ctype
                            GROUP BY author_id, content_type
                            ON CONFLICT (author_id, content_type, slug) DO UPDATE SET count = EXCLUDED.count
                            """
                        ),
                        {"fslug": fslug, "tslug": tslug, "ctype": content_type},
                    )
                # Remove old slug rows
                await conn.execute(
                    text("DELETE FROM product_tag_usage_counters WHERE slug = :fslug"),
                    {"fslug": fslug},
                )
                # Delete old tag
                await conn.execute(
                    text("DELETE FROM product_tag WHERE id = :id"), {"id": from_id}
                )
            return report

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]


__all__ = ["SQLAdminRepo"]
