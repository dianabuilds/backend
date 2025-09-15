from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from apps.backendDDD.app.api_gateway.routers import get_container
from apps.backendDDD.domains.platform.iam.security import get_current_user


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/tags")

    @router.get("", summary="List tags for current user")
    def list_tags(
        req: Request,
        q: str | None = Query(default=None),
        popular: bool = Query(default=False),
        limit: int = Query(default=10, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        type_: str | None = Query(default="all"),
        container=Depends(get_container),
        claims=Depends(get_current_user),
    ):
        uid = str(claims.get("sub")) if claims else None
        if not uid:
            return []
        svc = container.tags_service
        ctype = (type_ or "all").lower()
        if ctype not in ("all", "node", "quest"):
            ctype = "all"
        items = svc.list_for_user(uid, q, popular, limit, offset, content_type=ctype)
        return [dict(slug=i.slug, name=i.name, count=i.count) for i in items]

    return router
