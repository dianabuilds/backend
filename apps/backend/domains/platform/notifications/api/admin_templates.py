from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from apps.backend.app.api_gateway.routers import get_container
from domains.platform.iam.security import csrf_protect, require_admin
from domains.platform.notifications.application.template_use_cases import (
    delete_template as delete_template_use_case,
)
from domains.platform.notifications.application.template_use_cases import (
    get_template as get_template_use_case,
)
from domains.platform.notifications.application.template_use_cases import (
    list_templates as list_templates_use_case,
)
from domains.platform.notifications.application.template_use_cases import (
    upsert_template as upsert_template_use_case,
)
from packages.fastapi_rate_limit import optional_rate_limiter

_TEMPLATE_NOT_FOUND = "template_not_found"


def _value_error_to_http(error: ValueError) -> None:
    detail = str(error) or "bad_request"
    status = 404 if detail == _TEMPLATE_NOT_FOUND else 400
    raise HTTPException(status_code=status, detail=detail) from error


class TemplatePayload(BaseModel):
    id: str | None = None
    slug: str | None = None
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
        dependencies=(optional_rate_limiter(times=60, seconds=60)),
    )
    async def list_templates(
        req: Request,
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        svc = get_container(req).notifications.templates
        result = await list_templates_use_case(svc, limit=limit, offset=offset)
        return result

    @router.post(
        "/templates",
        dependencies=(optional_rate_limiter(times=20, seconds=60)),
    )
    async def upsert_template(
        req: Request,
        payload: TemplatePayload,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        svc = get_container(req).notifications.templates
        try:
            result = await upsert_template_use_case(
                svc, payload.model_dump(exclude_none=True, exclude_unset=True)
            )
        except ValueError as exc:
            _value_error_to_http(exc)
        except IntegrityError as exc:
            raise HTTPException(
                status_code=409, detail="template slug already exists"
            ) from exc
        return result

    @router.get(
        "/templates/{template_id}",
        dependencies=(optional_rate_limiter(times=60, seconds=60)),
    )
    async def get_template(
        req: Request,
        template_id: str,
        _admin: None = Depends(require_admin),
    ) -> dict[str, Any]:
        svc = get_container(req).notifications.templates
        result = await get_template_use_case(svc, template_id)
        if result is None:
            raise HTTPException(status_code=404, detail=_TEMPLATE_NOT_FOUND)
        return result

    @router.delete(
        "/templates/{template_id}",
        dependencies=(optional_rate_limiter(times=20, seconds=60)),
    )
    async def delete_template(
        req: Request,
        template_id: str,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        svc = get_container(req).notifications.templates
        return await delete_template_use_case(svc, template_id)

    return router


__all__ = ["make_router"]
