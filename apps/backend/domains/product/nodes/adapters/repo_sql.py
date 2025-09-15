from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from domains.product.nodes.application.ports import NodeDTO, Repo


class SQLNodesRepo(Repo):
    def __init__(self, engine: AsyncEngine | str) -> None:
        self._engine: AsyncEngine = (
            create_async_engine(str(engine)) if isinstance(engine, str) else engine
        )

    async def _aload_tags(self, node_ids: list[int]) -> dict[int, list[str]]:
        if not node_ids:
            return {}
        sql = text(
            "SELECT node_id, slug FROM product_node_tags WHERE node_id = ANY(:ids) ORDER BY slug"
        )
        async with self._engine.begin() as conn:
            rows = (await conn.execute(sql, {"ids": node_ids})).mappings().all()
        out: dict[int, list[str]] = {}
        for r in rows:
            nid = int(r["node_id"])  # type: ignore[redundant-cast]
            out.setdefault(nid, []).append(str(r["slug"]))
        return out

    def get(self, node_id: int) -> NodeDTO | None:
        import asyncio

        async def _run() -> NodeDTO | None:
            sql = text(
                "SELECT id, author_id::text AS author_id, title, is_public FROM product_nodes WHERE id = :id"
            )
            async with self._engine.begin() as conn:
                r = (await conn.execute(sql, {"id": int(node_id)})).mappings().first()
            if not r:
                return None
            tags = await self._aload_tags([int(node_id)])
            return NodeDTO(
                id=int(r["id"]),
                author_id=str(r["author_id"]),
                title=r["title"],
                tags=tags.get(int(node_id), []),
                is_public=bool(r["is_public"]),
            )

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]

    def set_tags(self, node_id: int, tags: Sequence[str]) -> NodeDTO:
        import asyncio

        async def _run() -> NodeDTO:
            # Replace tags atomically
            norm: list[str] = []
            seen: set[str] = set()
            for s in tags:
                v = str(s).strip().lower()
                if not v or v in seen:
                    continue
                seen.add(v)
                norm.append(v)
            async with self._engine.begin() as conn:
                # Ensure node exists
                chk = (
                    await conn.execute(
                        text("SELECT 1 FROM product_nodes WHERE id = :id"),
                        {"id": int(node_id)},
                    )
                ).first()
                if not chk:
                    raise ValueError("node not found")
                await conn.execute(
                    text("DELETE FROM product_node_tags WHERE node_id = :id"),
                    {"id": int(node_id)},
                )
                for s in norm:
                    await conn.execute(
                        text(
                            "INSERT INTO product_node_tags(node_id, slug) VALUES (:id, :slug) ON CONFLICT DO NOTHING"
                        ),
                        {"id": int(node_id), "slug": s},
                    )
            got = await self._araw_get(int(node_id))
            assert got is not None
            return got

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]

    def list_by_author(
        self, author_id: str, *, limit: int = 50, offset: int = 0
    ) -> list[NodeDTO]:
        import asyncio

        async def _run() -> list[NodeDTO]:
            sql = text(
                """
                SELECT id, author_id::text AS author_id, title, is_public
                FROM product_nodes
                WHERE author_id = cast(:aid as uuid)
                ORDER BY id ASC
                LIMIT :limit OFFSET :offset
                """
            )
            async with self._engine.begin() as conn:
                rows = (
                    (
                        await conn.execute(
                            sql,
                            {
                                "aid": str(author_id),
                                "limit": int(limit),
                                "offset": int(offset),
                            },
                        )
                    )
                    .mappings()
                    .all()
                )
            ids = [int(r["id"]) for r in rows]
            tagmap = await self._aload_tags(ids)
            out: list[NodeDTO] = []
            for r in rows:
                nid = int(r["id"])
                out.append(
                    NodeDTO(
                        id=nid,
                        author_id=str(r["author_id"]),
                        title=r["title"],
                        tags=tagmap.get(nid, []),
                        is_public=bool(r["is_public"]),
                    )
                )
            return out

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        else:
            return loop.run_until_complete(_run())  # type: ignore[misc]

    async def create(
        self,
        *,
        author_id: str,
        title: str | None,
        is_public: bool,
        tags: Sequence[str] | None = None,
    ) -> NodeDTO:
        async with self._engine.begin() as conn:
            r = (
                (
                    await conn.execute(
                        text(
                            "INSERT INTO product_nodes(author_id, title, is_public) VALUES (cast(:aid as uuid), :title, :pub) RETURNING id, author_id::text AS author_id, title, is_public"
                        ),
                        {"aid": author_id, "title": title, "pub": bool(is_public)},
                    )
                )
                .mappings()
                .first()
            )
            assert r is not None
            nid = int(r["id"])
            for s in tags or []:
                v = str(s).strip().lower()
                if not v:
                    continue
                await conn.execute(
                    text(
                        "INSERT INTO product_node_tags(node_id, slug) VALUES (:id, :slug) ON CONFLICT DO NOTHING"
                    ),
                    {"id": nid, "slug": v},
                )
        return await self._araw_get(nid)  # type: ignore[arg-type]

    async def update(
        self, node_id: int, *, title: str | None = None, is_public: bool | None = None
    ) -> NodeDTO:
        sets = []
        params: dict[str, object] = {"id": int(node_id)}
        if title is not None:
            sets.append("title = :title")
            params["title"] = title
        if is_public is not None:
            sets.append("is_public = :pub")
            params["pub"] = bool(is_public)
        if sets:
            sql = text(
                "UPDATE product_nodes SET "
                + ", ".join(sets)
                + ", updated_at = now() WHERE id = :id"
            )
            async with self._engine.begin() as conn:
                await conn.execute(sql, params)
        got = await self._araw_get(int(node_id))
        if not got:
            raise ValueError("node not found")
        return got

    async def delete(self, node_id: int) -> bool:
        async with self._engine.begin() as conn:
            res = await conn.execute(
                text("DELETE FROM product_nodes WHERE id = :id"), {"id": int(node_id)}
            )
            try:
                rc = res.rowcount  # type: ignore[attr-defined]
            except Exception:
                rc = None
        return bool(rc and rc > 0)

    # --- internal async helpers ---
    async def _araw_get(self, node_id: int) -> NodeDTO | None:
        sql = text(
            "SELECT id, author_id::text AS author_id, title, is_public FROM product_nodes WHERE id = :id"
        )
        async with self._engine.begin() as conn:
            r = (await conn.execute(sql, {"id": int(node_id)})).mappings().first()
        if not r:
            return None
        tags = await self._aload_tags([int(node_id)])
        return NodeDTO(
            id=int(r["id"]),
            author_id=str(r["author_id"]),
            title=r["title"],
            tags=tags.get(int(node_id), []),
            is_public=bool(r["is_public"]),
        )


__all__ = ["SQLNodesRepo"]
