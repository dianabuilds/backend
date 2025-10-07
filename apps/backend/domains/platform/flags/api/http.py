from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from apps.backend.app.api_gateway.routers import get_container
from domains.platform.flags.application.commands import (
    delete_flag as delete_flag_command,
)
from domains.platform.flags.application.commands import (
    upsert_flag as upsert_flag_command,
)
from domains.platform.flags.application.queries import (
    check_flag as check_flag_query,
)
from domains.platform.flags.application.queries import (
    list_flags as list_flags_query,
)
from domains.platform.iam.security import (
    csrf_protect,
    get_current_user,
    require_admin,
)
from packages.fastapi_rate_limit import optional_rate_limiter

logger = logging.getLogger(__name__)


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/flags", tags=["flags"])

    rate_limit = optional_rate_limiter(times=60, seconds=60)

    @router.get("", dependencies=tuple(rate_limit))
    async def list_flags(
        req: Request, _admin: None = Depends(require_admin)
    ) -> dict[str, Any]:
        container = get_container(req)
        return await list_flags_query(container.flags.service)

    mutate_limit = optional_rate_limiter(times=20, seconds=60)

    @router.post("", dependencies=tuple(mutate_limit))
    async def upsert_flag(
        req: Request,
        body: dict[str, Any],
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        if not isinstance(body, dict):
            raise HTTPException(status_code=400, detail="invalid_payload")
        if "slug" not in body:
            raise HTTPException(status_code=400, detail="slug_required")
        container = get_container(req)
        try:
            return await upsert_flag_command(container.flags.service, body)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.delete("/{slug}", dependencies=tuple(mutate_limit))
    async def delete_flag(
        req: Request,
        slug: str,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        container = get_container(req)
        return await delete_flag_command(container.flags.service, slug)

    @router.get("/check/{slug}")
    async def check_flag(
        req: Request, slug: str, claims=Depends(get_current_user)
    ) -> dict[str, Any]:
        container = get_container(req)
        return await check_flag_query(container.flags.service, slug, claims or {})

    return router


__all__ = ["make_router"]
