from __future__ import annotations

import asyncio
import os
import secrets
from collections.abc import Sequence

from sqlalchemy import Text, bindparam, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.product.nodes.application.ports import NodeDTO, Repo
from packages.core.db import get_async_engine


def _format_vector(values: Sequence[float] | None) -> str | None:
    if values is None:
        return None
    vec = [float(v) for v in values]
    target = _VECTOR_DIM
    if target and len(vec) > target:
        vec = vec[:target]
    elif target and len(vec) < target:
        vec = vec + [0.0] * (target - len(vec))
    return "[" + ", ".join(f"{val:.12g}" for val in vec) + "]"


def _parse_vector(value) -> list[float] | None:
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        vec = [float(v) for v in value]
    else:
        if isinstance(value, memoryview):
            value = value.tobytes().decode()
        elif isinstance(value, bytes):
            value = value.decode()
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                stripped = stripped[1:-1]
            if not stripped:
                vec = []
            else:
                parts = [
                    p.strip()
                    for p in stripped.replace(";", ",").split(",")
                    if p.strip()
                ]
                vec = [float(p) for p in parts]
        else:
            try:
                vec = [float(value)]
            except (TypeError, ValueError):
                return None
    target = _VECTOR_DIM
    if target and len(vec) > target:
        return vec[:target]
    if target and len(vec) < target:
        return vec + [0.0] * (target - len(vec))
    return vec


_DATETIME_FMT = 'YYYY-MM-DD""T""HH24:MI:SS""Z""'


_VECTOR_DIM_DEFAULT = 1536
try:
    _VECTOR_DIM = int(
        os.getenv("EMBEDDING_DIM")
        or os.getenv("APP_EMBEDDING_DIM")
        or _VECTOR_DIM_DEFAULT
    )
    if _VECTOR_DIM <= 0:
        _VECTOR_DIM = _VECTOR_DIM_DEFAULT
except (TypeError, ValueError):
    _VECTOR_DIM = _VECTOR_DIM_DEFAULT
_VECTOR_SQL_TYPE = f"vector({_VECTOR_DIM})"


class SQLNodesRepo(Repo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        if isinstance(engine, AsyncEngine):
            self._engine = engine
        else:
            self._engine = get_async_engine("nodes", url=engine)

    async def _load_tags(self, conn, node_ids: Sequence[int]) -> dict[int, list[str]]:
        if not node_ids:
            return {}
        rows = (
            (
                await conn.execute(
                    text(
                        "SELECT node_id, slug FROM product_node_tags WHERE node_id = ANY(:ids) ORDER BY slug"
                    ),
                    {"ids": list(map(int, node_ids))},
                )
            )
            .mappings()
            .all()
        )
        tags: dict[int, list[str]] = {}
        for row in rows:
            tags.setdefault(int(row["node_id"]), []).append(str(row["slug"]))
        return tags

    def _row_to_dto(self, row, tags: Sequence[str]) -> NodeDTO:
        return NodeDTO(
            id=int(row["id"]),
            slug=row.get("slug"),
            author_id=str(row["author_id"]),
            title=row.get("title"),
            tags=list(tags),
            is_public=bool(row["is_public"]),
            status=row.get("status"),
            publish_at=row.get("publish_at"),
            unpublish_at=row.get("unpublish_at"),
            content_html=row.get("content_html"),
            cover_url=row.get("cover_url"),
            embedding=_parse_vector(row.get("embedding")),
        )

    async def create(
        self,
        *,
        author_id: str,
        title: str | None,
        is_public: bool,
        tags: Sequence[str] | None = None,
        status: str | None = None,
        publish_at: str | None = None,
        unpublish_at: str | None = None,
        content_html: str | None = None,
        cover_url: str | None = None,
        embedding: Sequence[float] | None = None,
    ) -> NodeDTO:
        derived_status = status or ("published" if is_public else "draft")
        for _ in range(5):
            slug = secrets.token_hex(8)
            params = {
                "aid": author_id,
                "slug": slug,
                "title": title,
                "pub": bool(is_public),
                "status": derived_status,
                "pub_at": publish_at,
                "unpub_at": unpublish_at,
                "content": content_html,
                "cover": cover_url,
                "embedding": _format_vector(embedding),
            }
            try:
                async with self._engine.begin() as conn:
                    stmt_sql = f"""
                        INSERT INTO nodes(author_id, slug, title, is_public, status, publish_at, unpublish_at, content_html, cover_url, embedding)
                        VALUES (cast(:aid as uuid), :slug, :title, :pub, :status, :pub_at, :unpub_at, :content, :cover, CASE WHEN :embedding IS NULL THEN NULL ELSE CAST(:embedding AS {_VECTOR_SQL_TYPE}) END)
                        RETURNING id,
                                  slug,
                                  author_id::text AS author_id,
                                  title,
                                  is_public,
                                  status,
                                  to_char(publish_at, :fmt) AS publish_at,
                                  to_char(unpublish_at, :fmt) AS unpublish_at,
                                  content_html,
                                  cover_url,
                                  embedding
                    """
                    stmt = text(stmt_sql).bindparams(bindparam("embedding", type_=Text))
                    row = (
                        (await conn.execute(stmt, {**params, "fmt": _DATETIME_FMT}))
                        .mappings()
                        .first()
                    )
                    if row is None:
                        continue
                    norm_tags = []
                    for item in tags or []:
                        val = str(item).strip().lower()
                        if not val:
                            continue
                        norm_tags.append(val)
                        await conn.execute(
                            text(
                                "INSERT INTO product_node_tags(node_id, slug) VALUES (:id, :slug) ON CONFLICT DO NOTHING"
                            ),
                            {"id": int(row["id"]), "slug": val},
                        )
                    return self._row_to_dto(row, norm_tags)
            except IntegrityError:
                continue
        raise RuntimeError("failed to generate unique slug for node")

    def get(self, node_id: int) -> NodeDTO | None:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self._araw_get(node_id))
        raise RuntimeError(
            "SQLNodesRepo.get cannot be called while an event loop is running; use await SQLNodesRepo._araw_get instead"
        )

    def get_by_slug(self, slug: str) -> NodeDTO | None:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self._araw_get_by_slug(slug))
        raise RuntimeError(
            "SQLNodesRepo.get_by_slug cannot be called while an event loop is running; use await SQLNodesRepo._araw_get_by_slug instead"
        )

    async def _araw_get_by_slug(self, slug: str) -> NodeDTO | None:
        async with self._engine.begin() as conn:
            row = (
                (
                    await conn.execute(
                        text(
                            """
                        SELECT id,
                               slug,
                               author_id::text AS author_id,
                               title,
                               is_public,
                               status,
                               to_char(publish_at, :fmt) AS publish_at,
                               to_char(unpublish_at, :fmt) AS unpublish_at,
                               content_html,
                               cover_url,
                               embedding
                        FROM nodes
                        WHERE slug = :slug
                        """
                        ),
                        {"slug": str(slug), "fmt": _DATETIME_FMT},
                    )
                )
                .mappings()
                .first()
            )
            if row is None:
                return None
            tags = await self._load_tags(conn, [int(row["id"])])
            return self._row_to_dto(row, tags.get(int(row["id"]), []))

    def set_tags(self, node_id: int, tags: Sequence[str]) -> NodeDTO:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self._aset_tags(node_id, tags))
        raise RuntimeError(
            "SQLNodesRepo.set_tags cannot be called while an event loop is running; use await SQLNodesRepo._aset_tags instead"
        )

    async def _aset_tags(self, node_id: int, tags: Sequence[str]) -> NodeDTO:
        normalized: list[str] = []
        seen: set[str] = set()
        for item in tags:
            value = str(item).strip().lower()
            if not value or value in seen:
                continue
            seen.add(value)
            normalized.append(value)
        async with self._engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM product_node_tags WHERE node_id = :id"),
                {"id": int(node_id)},
            )
            for value in normalized:
                await conn.execute(
                    text(
                        "INSERT INTO product_node_tags(node_id, slug) VALUES (:id, :slug) ON CONFLICT DO NOTHING"
                    ),
                    {"id": int(node_id), "slug": value},
                )
        got = await self._araw_get(node_id)
        if got is None:
            raise ValueError("node not found")
        return got

    def list_by_author(
        self, author_id: str, *, limit: int = 50, offset: int = 0
    ) -> list[NodeDTO]:
        import asyncio

        async def _run() -> list[NodeDTO]:
            async with self._engine.begin() as conn:
                rows = (
                    (
                        await conn.execute(
                            text(
                                """
                            SELECT id,
                                   slug,
                                   author_id::text AS author_id,
                                   title,
                                   is_public,
                                   status,
                                   to_char(publish_at, :fmt) AS publish_at,
                                   to_char(unpublish_at, :fmt) AS unpublish_at,
                                   content_html,
                                   cover_url,
                                   embedding
                            FROM nodes
                            WHERE author_id = cast(:aid as uuid)
                            ORDER BY id ASC
                            LIMIT :limit OFFSET :offset
                            """
                            ),
                            {
                                "aid": str(author_id),
                                "limit": int(limit),
                                "offset": int(offset),
                                "fmt": _DATETIME_FMT,
                            },
                        )
                    )
                    .mappings()
                    .all()
                )
                node_ids = [int(row["id"]) for row in rows]
                tags_map = await self._load_tags(conn, node_ids)
                return [
                    self._row_to_dto(row, tags_map.get(int(row["id"]), []))
                    for row in rows
                ]

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        raise RuntimeError(
            "SQLNodesRepo.list_by_author cannot be called while an event loop is running; use an async variant instead"
        )

    async def search_by_embedding(
        self, embedding: Sequence[float], *, limit: int = 64
    ) -> list[NodeDTO]:
        async with self._engine.begin() as conn:
            stmt_sql = f"""
                SELECT id,
                       slug,
                       author_id::text AS author_id,
                       title,
                       is_public,
                       status,
                       to_char(publish_at, :fmt) AS publish_at,
                       to_char(unpublish_at, :fmt) AS unpublish_at,
                       content_html,
                       cover_url,
                       embedding
                FROM nodes
                WHERE embedding IS NOT NULL
                ORDER BY embedding <-> CAST(:embedding AS {_VECTOR_SQL_TYPE})
                LIMIT :limit
            """
            stmt = text(stmt_sql).bindparams(bindparam("embedding", type_=Text))
            rows = (
                (
                    await conn.execute(
                        stmt,
                        {
                            "embedding": _format_vector(embedding),
                            "limit": int(limit),
                            "fmt": _DATETIME_FMT,
                        },
                    )
                )
                .mappings()
                .all()
            )
            node_ids = [int(row["id"]) for row in rows]
            tags_map = await self._load_tags(conn, node_ids)
            return [
                self._row_to_dto(row, tags_map.get(int(row["id"]), [])) for row in rows
            ]

    async def update(
        self,
        node_id: int,
        *,
        title: str | None = None,
        is_public: bool | None = None,
        status: str | None = None,
        publish_at: str | None = None,
        unpublish_at: str | None = None,
        content_html: str | None = None,
        cover_url: str | None = None,
        embedding: Sequence[float] | None = None,
    ) -> NodeDTO:
        sets: list[str] = []
        params: dict[str, object] = {"id": int(node_id), "fmt": _DATETIME_FMT}
        if title is not None:
            sets.append("title = :title")
            params["title"] = title
        if is_public is not None:
            sets.append("is_public = :pub")
            params["pub"] = bool(is_public)
        if status is not None:
            sets.append("status = :status")
            params["status"] = status
        if publish_at is not None:
            sets.append("publish_at = :pub_at")
            params["pub_at"] = publish_at
        if unpublish_at is not None:
            sets.append("unpublish_at = :unpub_at")
            params["unpub_at"] = unpublish_at
        if content_html is not None:
            sets.append("content_html = :content")
            params["content"] = content_html
        if cover_url is not None:
            sets.append("cover_url = :cover")
            params["cover"] = cover_url
        if embedding is not None:
            embedding_clause = f"embedding = CASE WHEN :embedding IS NULL THEN NULL ELSE CAST(:embedding AS {_VECTOR_SQL_TYPE}) END"
            sets.append(embedding_clause)
            params["embedding"] = _format_vector(embedding)
        if sets:
            sets.append("updated_at = now()")
            async with self._engine.begin() as conn:
                stmt = text("UPDATE nodes SET " + ", ".join(sets) + " WHERE id = :id")
                if "embedding" in params:
                    stmt = stmt.bindparams(bindparam("embedding", type_=Text))
                await conn.execute(stmt, params)
        dto = await self._araw_get(node_id)
        if dto is None:
            raise ValueError("node not found")
        return dto

    async def delete(self, node_id: int) -> bool:
        async with self._engine.begin() as conn:
            res = await conn.execute(
                text(
                    "UPDATE nodes SET status = 'deleted', is_public = false, updated_at = now() WHERE id = :id AND status <> 'deleted'"
                ),
                {"id": int(node_id)},
            )
            affected = getattr(res, "rowcount", None)  # type: ignore[attr-defined]
        return bool(affected and affected > 0)

    async def _araw_get(self, node_id: int) -> NodeDTO | None:
        async with self._engine.begin() as conn:
            row = (
                (
                    await conn.execute(
                        text(
                            """
                        SELECT id,
                               slug,
                               author_id::text AS author_id,
                               title,
                               is_public,
                               status,
                               to_char(publish_at, :fmt) AS publish_at,
                               to_char(unpublish_at, :fmt) AS unpublish_at,
                               content_html,
                               cover_url,
                               embedding
                        FROM nodes
                        WHERE id = :id
                        """
                        ),
                        {"id": int(node_id), "fmt": _DATETIME_FMT},
                    )
                )
                .mappings()
                .first()
            )
            if row is None:
                return None
            tags = await self._load_tags(conn, [int(node_id)])
            return self._row_to_dto(row, tags.get(int(node_id), []))
