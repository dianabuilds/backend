from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from apps.backendDDD.domains.platform.search.ports import (
    Doc,
    Hit,
    IndexPort,
    QueryPort,
    SearchCache,
    SearchPersistence,
)


@dataclass
class SearchService:
    index: IndexPort
    query: QueryPort
    cache: SearchCache | None = None
    persist: SearchPersistence | None = None

    async def upsert(self, doc: Doc) -> None:
        await self.index.upsert(doc)
        if self.cache:
            await self.cache.bump_version()
        if self.persist:
            docs = await self.index.list_all()
            await self.persist.save(docs)

    async def delete(self, id: str) -> None:  # noqa: A002 - id name OK here
        await self.index.delete(id)
        if self.cache:
            await self.cache.bump_version()
        if self.persist:
            docs = await self.index.list_all()
            await self.persist.save(docs)

    async def search(
        self,
        q: str,
        *,
        tags: Sequence[str] | None,
        match: str = "any",
        limit: int = 20,
        offset: int = 0,
    ) -> list[Hit]:
        if not self.cache:
            return await self.query.search(
                q, tags=tags, match=match, limit=limit, offset=offset
            )
        # cache key
        norm_tags = ",".join(
            sorted(t.strip().lower() for t in (tags or []) if t.strip())
        )
        raw_key = f"q={ (q or '').strip().lower() }|tags={norm_tags}|m={match}|l={limit}|o={offset}"
        key = await self.cache.versioned_key(raw_key)
        cached = await self.cache.get(key)
        if cached is not None:
            return cached
        hits = await self.query.search(
            q, tags=tags, match=match, limit=limit, offset=offset
        )
        await self.cache.set(key, hits)
        return hits


__all__ = ["SearchService"]
