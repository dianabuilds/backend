from __future__ import annotations

import logging

from sqlalchemy import Integer, String, bindparam, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.product.tags.application.admin_ports import AdminRepo
from domains.product.tags.domain.admin_models import (
    AliasView,
    BlacklistItem,
    TagGroupSummary,
    TagListItem,
)
from packages.core.async_utils import run_sync
from packages.core.db import get_async_engine
from packages.core.sql_fallback import evaluate_sql_backend

from .admin_repo_memory import MemoryAdminRepo
from .store_memory import TagUsageStore

logger = logging.getLogger(__name__)


class SQLAdminRepo(AdminRepo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        if isinstance(engine, AsyncEngine):
            self._engine = engine
        else:
            self._engine = get_async_engine("tags-admin", url=engine)
        # Lazy-detected table names to support different schemas
        self._tbl_tag: str | None = None
        self._tbl_usage: str | None = None
        self._tbl_alias: str | None = None

    async def _ensure_introspected(self, conn) -> None:
        if self._tbl_tag is not None:
            return
        rows = (
            await conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
                )
            )
        ).fetchall()
        names = {str(r[0]) for r in rows}
        # Tag table (prefer canonical 'tags' if both exist)
        if "tags" in names:
            self._tbl_tag = "tags"
        elif "tag" in names:
            self._tbl_tag = "tag"
        else:
            # Fall back to an obviously missing table to surface error early
            self._tbl_tag = "tag"
        # Optional tables
        self._tbl_usage = (
            "tag_usage_counters" if "tag_usage_counters" in names else None
        )
        self._tbl_alias = "tag_alias" if "tag_alias" in names else None

    async def _exists_tag(self, tag_id: str) -> bool:
        async with self._engine.begin() as conn:
            await self._ensure_introspected(conn)
            sql = text(f"SELECT 1 FROM {self._tbl_tag or 'tag'} WHERE id = :id")
            row = (await conn.execute(sql, {"id": tag_id})).first()
            return bool(row)

    def list_with_counters(
        self, q: str | None, limit: int, offset: int, content_type: str | None = None
    ) -> list[TagListItem]:
        async def _run() -> list[TagListItem]:
            async with self._engine.begin() as conn:
                await self._ensure_introspected(conn)
                tag_tbl = self._tbl_tag or "tag"
                # Build dynamic SQL parts
                usage_cte = (
                    f"WITH usage AS (SELECT slug, SUM(count)::int AS usage_count FROM {self._tbl_usage} WHERE (:ctype IS NULL OR content_type = CAST(:ctype AS text)) GROUP BY slug)"
                    if self._tbl_usage
                    else "WITH usage AS (SELECT NULL::text AS slug, 0::int AS usage_count WHERE false)"
                )
                alias_cte = (
                    f", alia AS (SELECT tag_id, COUNT(*)::int AS aliases_count FROM {self._tbl_alias} GROUP BY tag_id)"
                    if self._tbl_alias
                    else ", alia AS (SELECT NULL::uuid AS tag_id, 0::int AS aliases_count WHERE false)"
                )
                sql = text(
                    f"""
                    {usage_cte}
                    {alias_cte}
                    SELECT t.id, t.slug, t.name, t.created_at, t.is_hidden,
                           COALESCE(u.usage_count, 0) AS usage_count,
                           COALESCE(a.aliases_count, 0) AS aliases_count
                    FROM {tag_tbl} t
                    LEFT JOIN usage u ON u.slug = t.slug
                    LEFT JOIN alia a ON a.tag_id::text = t.id::text
                    WHERE (:q IS NULL OR t.slug ILIKE ('%' || :q || '%') OR t.name ILIKE ('%' || :q || '%'))
                    ORDER BY t.name ASC, t.slug ASC
                    LIMIT :limit OFFSET :offset
                    """
                ).bindparams(
                    bindparam("q", type_=String),
                    bindparam("limit", type_=Integer),
                    bindparam("offset", type_=Integer),
                    bindparam("ctype", type_=String),
                )
                # Treat empty string as NULL to disable filter
                q_val = None if (q is None or str(q).strip() == "") else str(q)
                ctype_val = (
                    None
                    if (content_type is None or str(content_type).strip() == "")
                    else str(content_type)
                )
                params = {
                    "q": q_val,
                    "limit": int(limit),
                    "offset": int(offset),
                    "ctype": ctype_val,
                }
                rows = (await conn.execute(sql, params)).mappings().all()
                return [
                    TagListItem(
                        id=str(r["id"]),
                        slug=str(r["slug"]),
                        name=str(r["name"]),
                        created_at=r["created_at"],
                        is_hidden=bool(r.get("is_hidden", False)),
                        usage_count=int(r.get("usage_count", 0)),
                        aliases_count=int(r.get("aliases_count", 0)),
                    )
                    for r in rows
                ]

        return run_sync(_run())

    def list_groups(self) -> list[TagGroupSummary]:
        async def _run() -> list[TagGroupSummary]:
            async with self._engine.begin() as conn:
                await self._ensure_introspected(conn)
                if not self._tbl_usage:
                    return []
                sql = text(
                    f"""
                    SELECT content_type,
                           COUNT(DISTINCT slug)::int AS tag_count,
                           SUM(count)::bigint AS usage_count,
                           COUNT(DISTINCT author_id)::int AS author_count
                      FROM {self._tbl_usage}
                  GROUP BY content_type
                  ORDER BY usage_count DESC, content_type ASC
                    """
                )
                rows = (await conn.execute(sql)).mappings().all()
                return [
                    TagGroupSummary(
                        key=str(r.get("content_type") or "all"),
                        tag_count=int(r.get("tag_count") or 0),
                        usage_count=int(r.get("usage_count") or 0),
                        author_count=int(r.get("author_count") or 0),
                    )
                    for r in rows
                ]

        return run_sync(_run())

    def list_aliases(self, tag_id: str) -> list[AliasView]:
        async def _run() -> list[AliasView]:
            async with self._engine.begin() as conn:
                await self._ensure_introspected(conn)
                if not self._tbl_alias:
                    return []
                sql = text(
                    f"SELECT id, tag_id, alias, type, created_at FROM {self._tbl_alias} WHERE tag_id = :tid ORDER BY created_at DESC"
                )
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

        return run_sync(_run())

    def add_alias(self, tag_id: str, alias: str) -> AliasView:
        async def _run() -> AliasView:
            if not await self._exists_tag(tag_id):
                raise ValueError("tag_not_found")
            async with self._engine.begin() as conn:
                await self._ensure_introspected(conn)
                if not self._tbl_alias:
                    raise ValueError("aliases_unsupported")
                sql = text(
                    f"""
                    INSERT INTO {self._tbl_alias}(tag_id, alias, type)
                    VALUES (:tid, :alias, 'alias')
                    RETURNING id, tag_id, alias, type, created_at
                    """
                )
                try:
                    r = (
                        (await conn.execute(sql, {"tid": tag_id, "alias": alias}))
                        .mappings()
                        .first()
                    )
                except IntegrityError as exc:
                    raise ValueError("alias_conflict") from exc
                assert r is not None
                return AliasView(
                    id=str(r["id"]),
                    tag_id=str(r["tag_id"]),
                    alias=str(r["alias"]),
                    type=str(r["type"]),
                    created_at=r["created_at"],
                )

        return run_sync(_run())

    def remove_alias(self, alias_id: str) -> None:
        async def _run() -> None:
            async with self._engine.begin() as conn:
                await self._ensure_introspected(conn)
                if not self._tbl_alias:
                    return None
                sql = text(f"DELETE FROM {self._tbl_alias} WHERE id = :id")
                await conn.execute(sql, {"id": alias_id})

        run_sync(_run())

    def blacklist_list(self, q: str | None) -> list[BlacklistItem]:
        async def _run() -> list[BlacklistItem]:
            base = "SELECT slug, reason, created_at FROM tag_blacklist"
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

        return run_sync(_run())

    def blacklist_add(self, slug: str, reason: str | None) -> BlacklistItem:
        async def _run() -> BlacklistItem:
            sql = text(
                """
                INSERT INTO tag_blacklist(slug, reason)
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

        return run_sync(_run())

    def blacklist_delete(self, slug: str) -> None:
        async def _run() -> None:
            sql = text("DELETE FROM tag_blacklist WHERE slug = :slug")
            async with self._engine.begin() as conn:
                await conn.execute(sql, {"slug": slug})

        run_sync(_run())

    def create_tag(self, slug: str, name: str) -> TagListItem:
        async def _run() -> TagListItem:
            sql = text(
                """
                INSERT INTO tag(slug, name) VALUES (:slug, :name)
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
                    "SELECT COALESCE(SUM(count),0)::int AS c FROM tag_usage_counters WHERE slug = :slug"
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

        return run_sync(_run())

    def delete_tag(self, tag_id: str) -> None:
        async def _run() -> None:
            # Capture slug then delete tag and related data
            async with self._engine.begin() as conn:
                r = (
                    (
                        await conn.execute(
                            text("SELECT slug FROM tag WHERE id = :id"),
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
                    text("DELETE FROM tag WHERE id = :id"), {"id": tag_id}
                )
                await conn.execute(
                    text("DELETE FROM tag_usage_counters WHERE slug = :slug"),
                    {"slug": slug},
                )

        run_sync(_run())

    async def _merge_dry_run(
        self, from_id: str, to_id: str, content_type: str | None
    ) -> dict:
        sql = text("SELECT id, slug, name FROM tag WHERE id = :id")
        async with self._engine.begin() as conn:
            f = (await conn.execute(sql, {"id": from_id})).mappings().first()
            t = (await conn.execute(sql, {"id": to_id})).mappings().first()
            if not f or not t:
                return {"errors": ["tag not found"], "warnings": []}
            cnt_sql = text(
                "SELECT COALESCE(SUM(count),0)::int AS c FROM tag_usage_counters WHERE slug = :slug AND (:ctype IS NULL OR content_type = :ctype)"
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
                            "SELECT COUNT(*)::int AS n FROM tag_alias WHERE tag_id = :tid"
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

    def merge_dry_run(
        self, from_id: str, to_id: str, content_type: str | None = None
    ) -> dict:
        return run_sync(self._merge_dry_run(from_id, to_id, content_type))

    def merge_apply(
        self,
        from_id: str,
        to_id: str,
        actor_id: str | None,
        reason: str | None,
        content_type: str | None = None,
    ) -> dict:
        async def _run() -> dict:
            report = await self._merge_dry_run(from_id, to_id, content_type)
            if report.get("errors"):
                return report
            async with self._engine.begin() as conn:
                # Re-fetch slugs for safety
                sel = text("SELECT id, slug FROM tag WHERE id = :id")
                f = (await conn.execute(sel, {"id": from_id})).mappings().first()
                t = (await conn.execute(sel, {"id": to_id})).mappings().first()
                if not f or not t:
                    return report
                fslug = str(f["slug"])
                tslug = str(t["slug"])
                # Move aliases
                await conn.execute(
                    text("UPDATE tag_alias SET tag_id = :tid WHERE tag_id = :fid"),
                    {"tid": to_id, "fid": from_id},
                )
                # Merge usage counters
                if content_type is None:
                    # merge across all content types
                    await conn.execute(
                        text(
                            """
                            INSERT INTO tag_usage_counters(author_id, content_type, slug, count)
                            SELECT author_id, content_type, :tslug AS slug, SUM(count) AS count
                            FROM tag_usage_counters
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
                            INSERT INTO tag_usage_counters(author_id, content_type, slug, count)
                            SELECT author_id, content_type, :tslug AS slug, SUM(count) AS count
                            FROM tag_usage_counters
                            WHERE slug IN (:fslug, :tslug) AND content_type = :ctype
                            GROUP BY author_id, content_type
                            ON CONFLICT (author_id, content_type, slug) DO UPDATE SET count = EXCLUDED.count
                            """
                        ),
                        {"fslug": fslug, "tslug": tslug, "ctype": content_type},
                    )
                # Remove old slug rows
                await conn.execute(
                    text("DELETE FROM tag_usage_counters WHERE slug = :fslug"),
                    {"fslug": fslug},
                )
                # Delete old tag
                await conn.execute(
                    text("DELETE FROM tag WHERE id = :id"), {"id": from_id}
                )
            return report

        return run_sync(_run())


def _log_fallback(reason: str | None, error: Exception | None = None) -> None:
    if error is not None:
        logger.warning(
            "tags admin repo: falling back to memory due to SQL error: %s", error
        )
        return
    if not reason:
        logger.debug("tags admin repo: using memory backend")
        return
    level = logging.DEBUG
    lowered = reason.lower()
    if "invalid" in lowered or "empty" in lowered:
        level = logging.WARNING
    elif "not configured" in lowered or "helpers unavailable" in lowered:
        level = logging.INFO
    logger.log(level, "tags admin repo: using memory backend (%s)", reason)


def create_repo(settings, *, store: TagUsageStore | None = None) -> AdminRepo:
    decision = evaluate_sql_backend(settings)
    if not decision.dsn:
        _log_fallback(decision.reason)
        return MemoryAdminRepo(store or TagUsageStore())
    try:
        return SQLAdminRepo(decision.dsn)
    except Exception as exc:  # pragma: no cover - defensive fallback
        _log_fallback(decision.reason or "engine initialization failed", error=exc)
        return MemoryAdminRepo(store or TagUsageStore())


__all__ = [
    "SQLAdminRepo",
    "create_repo",
]
