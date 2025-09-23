from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

try:
    from fastapi_limiter.depends import RateLimiter  # type: ignore
except Exception:  # pragma: no cover
    RateLimiter = None  # type: ignore

from apps.backend import get_container
from domains.platform.iam.security import csrf_protect, require_admin


class TemplatePayload(BaseModel):
    id: str | None = None
    slug: str
    name: str
    body: str
    description: str | None = None
    subject: str | None = None
    locale: str | None = None
    variables: dict[str, Any] | None = None
    meta: dict[str, Any] | None = None
    created_by: str | None = None


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/notifications/admin", tags=["admin-notifications"])

    @router.get(
        "/templates",
        dependencies=([Depends(RateLimiter(times=60, seconds=60))] if RateLimiter else []),
    )
    async def list_templates(
        req: Request,
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        svc = get_container(req).notifications.templates
        items = await svc.list(limit=limit, offset=offset)
        return {"items": [asdict(t) for t in items]}

    @router.post(
        "/templates",
        dependencies=([Depends(RateLimiter(times=20, seconds=60))] if RateLimiter else []),
    )
    async def upsert_template(
        req: Request,
        payload: TemplatePayload,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        svc = get_container(req).notifications.templates
        try:
            tmpl = await svc.save(payload.model_dump())
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except IntegrityError as exc:
            raise HTTPException(status_code=409, detail="template slug already exists") from exc
        return {"template": asdict(tmpl)}

    @router.get(
        "/templates/{template_id}",
        dependencies=([Depends(RateLimiter(times=60, seconds=60))] if RateLimiter else []),
    )
    async def get_template(
        req: Request,
        template_id: str,
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        svc = get_container(req).notifications.templates
        tmpl = await svc.get(template_id)
        if not tmpl:
            raise HTTPException(status_code=404, detail="template_not_found")
        return {"template": asdict(tmpl)}

    @router.delete(
        "/templates/{template_id}",
        dependencies=([Depends(RateLimiter(times=20, seconds=60))] if RateLimiter else []),
    )
    async def delete_template(
        req: Request,
        template_id: str,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        svc = get_container(req).notifications.templates
        await svc.delete(template_id)
        return {"ok": True}

    return router


__all__ = ["make_router"]
