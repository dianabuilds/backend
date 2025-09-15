from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

try:
    from fastapi_limiter.depends import RateLimiter  # type: ignore
except Exception:  # pragma: no cover
    RateLimiter = None  # type: ignore

from apps.backend import get_container
from domains.platform.iam.security import (
    csrf_protect,
    get_current_user,
    require_admin,
)


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/flags", tags=["flags"])

    @router.get(
        "",
        dependencies=(
            [Depends(RateLimiter(times=60, seconds=60))] if RateLimiter else []
        ),
    )
    async def list_flags(
        req: Request, _admin: None = Depends(require_admin)
    ) -> dict[str, Any]:
        c = get_container(req)
        items = await c.flags.service.list()
        return {"items": [f.__dict__ for f in items]}

    @router.post(
        "",
        dependencies=(
            [Depends(RateLimiter(times=20, seconds=60))] if RateLimiter else []
        ),
    )
    async def upsert_flag(
        req: Request,
        body: dict[str, Any],
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        c = get_container(req)
        if "slug" not in body:
            raise HTTPException(status_code=400, detail="slug_required")
        f = await c.flags.service.upsert(body)
        return {"flag": f.__dict__}

    @router.delete(
        "/{slug}",
        dependencies=(
            [Depends(RateLimiter(times=20, seconds=60))] if RateLimiter else []
        ),
    )
    async def delete_flag(
        req: Request,
        slug: str,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        c = get_container(req)
        await c.flags.service.delete(slug)
        return {"ok": True}

    @router.get("/check/{slug}")
    async def check_flag(
        req: Request, slug: str, claims=Depends(get_current_user)
    ) -> dict[str, Any]:
        c = get_container(req)
        on = await c.flags.service.evaluate(slug, claims or {})
        return {"slug": slug, "on": bool(on)}

    return router
