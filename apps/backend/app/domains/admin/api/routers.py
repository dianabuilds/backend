from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.core.feature_flags import get_effective_flags
from app.domains.admin.application.menu_service import (
    count_items,
    get_cached_menu,
    invalidate_menu_cache,
)
from app.domains.users.infrastructure.models.user import User
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

logger = logging.getLogger(__name__)

admin_required = require_admin_role({"admin", "moderator"})

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.get("/menu", summary="Get admin menu")
async def get_admin_menu(
    request: Request,
    current_user: Annotated[User, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> Response:
    preview_header = request.headers.get("X-Feature-Flags", "")
    effective_flags = await get_effective_flags(db, preview_header)
    flags: list[str] = sorted(list(effective_flags))

    menu, etag, cached = get_cached_menu(current_user, flags)
    if_none = request.headers.get("if-none-match")
    if if_none == etag:
        logger.info(
            "admin_menu",
            extra={
                "role": current_user.role,
                "items_count": count_items(menu.items),
                "served_from_cache": cached,
                "etag": etag,
            },
        )
        return Response(status_code=304, headers={"ETag": etag})

    payload = menu.model_dump(by_alias=True, mode="json")
    response = JSONResponse(payload)
    response.headers["ETag"] = etag
    logger.info(
        "admin_menu",
        extra={
            "role": current_user.role,
            "items_count": count_items(menu.items),
            "served_from_cache": cached,
            "etag": etag,
        },
    )
    return response


@router.post("/menu/invalidate", summary="Invalidate admin menu cache")
async def invalidate_admin_menu(
    current_user: Annotated[User, Depends(admin_required)] = ...,
) -> JSONResponse:
    invalidate_menu_cache()
    return JSONResponse({"status": "invalidated"})
