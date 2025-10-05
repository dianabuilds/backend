from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from domains.platform.search.ports import Doc, Hit, IndexPort, QueryPort
from packages.core.db import get_async_engine


class SQLSearchIndex(IndexPort, QueryPort):
    """Postgres-backed TF/TS vector search index."""

    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            engine
            if isinstance(engine, AsyncEngine)
            else get_async_engine("platform-search", url=engine)
        )

    async def upsert(self, doc: Doc) -> None:
        sql = text(
            """
            INSERT INTO search_documents (id, title, body, tags, tsv)
            VALUES (:id, :title, :body, CAST(:tags AS text[]),
                    to_tsvector('simple', :vector))
            ON CONFLICT (id) DO UPDATE SET
              title = EXCLUDED.title,
              body = EXCLUDED.body,
              tags = EXCLUDED.tags,
              tsv = EXCLUDED.tsv,
              updated_at = now()
            """
        )
        params = {
            "id": doc.id,
            "title": doc.title,
            "body": doc.text,
            "tags": list(doc.tags or ()),
            "vector": f"{doc.title}\n{doc.text}",
        }
        async with self._engine.begin() as conn:
            await conn.execute(sql, params)

    async def delete(self, id: str) -> None:  # noqa: A002 - id name OK here
        sql = text("DELETE FROM search_documents WHERE id = :id")
        async with self._engine.begin() as conn:
            await conn.execute(sql, {"id": id})

    async def list_all(self) -> list[Doc]:
        sql = text("SELECT id, title, body, tags FROM search_documents ORDER BY id")
        async with self._engine.begin() as conn:
            rows = (await conn.execute(sql)).mappings().all()
        docs: list[Doc] = []
        for row in rows:
            tags = tuple(row.get("tags") or [])
            docs.append(
                Doc(
                    id=str(row["id"]),
                    title=str(row["title"]),
                    text=str(row["body"]),
                    tags=tuple(str(t) for t in tags),
                )
            )
        return docs

    async def search(
        self,
        q: str,
        *,
        tags: Sequence[str] | None,
        match: str,
        limit: int,
        offset: int,
    ) -> list[Hit]:
        base_conditions: list[str] = []
        params: dict[str, object] = {
            "limit": int(limit),
            "offset": int(offset),
        }
        q = (q or "").strip()
        score_expr = "0.0 AS score"
        if q:
            score_expr = "ts_rank_cd(sd.tsv, plainto_tsquery('simple', :q)) AS score"
            base_conditions.append("sd.tsv @@ plainto_tsquery('simple', :q)")
            params["q"] = q
        tag_list = [str(t).strip().lower() for t in (tags or []) if str(t).strip()]
        if tag_list:
            params["tags"] = tag_list
            operator = "@>" if match == "all" else "&&"
            base_conditions.append(f"sd.tags {operator} CAST(:tags AS text[])")
        where_clause = (
            "WHERE " + " AND ".join(base_conditions) if base_conditions else ""
        )
        order_clause = (
            "ORDER BY score DESC, sd.updated_at DESC, sd.id ASC"
            if q
            else "ORDER BY sd.updated_at DESC, sd.id ASC"
        )
        sql = text(
            f"""
            SELECT sd.id,
                   sd.title,
                   sd.tags,
                   {score_expr}
              FROM search_documents AS sd
              {where_clause}
              {order_clause}
              LIMIT :limit OFFSET :offset
            """
        )
        async with self._engine.begin() as conn:
            rows = (await conn.execute(sql, params)).mappings().all()
        hits: list[Hit] = []
        for row in rows:
            tags_tuple = tuple(str(t) for t in (row.get("tags") or []))
            hits.append(
                Hit(
                    id=str(row["id"]),
                    score=float(row.get("score", 0.0)),
                    title=str(row.get("title") or ""),
                    tags=tags_tuple,
                )
            )
        return hits


__all__ = ["SQLSearchIndex"]
