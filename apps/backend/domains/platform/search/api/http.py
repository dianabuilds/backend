from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from apps.backend.app.api_gateway.routers import get_container
from domains.platform.iam.security import csrf_protect, require_admin
from domains.platform.search.application.stats_service import (
    search_stats,
)
from domains.platform.search.ports import Doc
from packages.fastapi_rate_limit import optional_rate_limiter


class IndexIn(BaseModel):
    id: str
    title: str
    text: str
    tags: list[str] = Field(default_factory=list)


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1", tags=["search"])

    @router.get("/search")
    async def search(
        req: Request,
        q: str | None = None,
        tags: str | None = Query(default=None),
        match: str = Query(default="any", pattern="^(any|all)$"),
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        c = get_container(req)
        tag_list: list[str] | None = None
        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        qq = q or ""
        hits = await c.search.service.search(
            qq, tags=tag_list, match=match, limit=limit, offset=offset
        )
        out = [
            {"id": h.id, "title": h.title, "tags": list(h.tags), "score": h.score}
            for h in hits
        ]
        search_stats.record(qq, len(out))
        return out

    @router.post(
        "/search/index",
        dependencies=(optional_rate_limiter(times=60, seconds=60)),
    )
    async def index(
        req: Request,
        body: IndexIn,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        c = get_container(req)
        await c.search.service.upsert(
            Doc(id=body.id, title=body.title, text=body.text, tags=tuple(body.tags))
        )
        return {"ok": True}

    @router.delete(
        "/search/{doc_id}",
        dependencies=(optional_rate_limiter(times=60, seconds=60)),
    )
    async def delete(
        req: Request,
        doc_id: str,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        c = get_container(req)
        await c.search.service.delete(doc_id)
        return {"ok": True}

    @router.get("/search/suggest")
    async def suggest(req: Request, q: str, limit: int = 10) -> list[str]:
        c = get_container(req)
        hits = await c.search.service.search(
            q, tags=None, match="any", limit=limit, offset=0
        )
        return [h.title for h in hits]

    @router.get("/search/stats/top")
    async def top_queries(limit: int = 10) -> list[dict[str, int | str]]:
        return search_stats.top(limit)

    return router
