from __future__ import annotations  # mypy: ignore-errors

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.admin.application.feature_flag_service import (
    ensure_known_flags,
    invalidate_cache,
    set_flag,
)
from app.domains.admin.application.menu_service import invalidate_menu_cache
from app.domains.admin.infrastructure.models.feature_flag import FeatureFlag
from app.domains.audit.application.audit_service import audit_log
from app.providers.db.session import get_db
from app.schemas.flags import FeatureFlagOut, FeatureFlagUpdateIn
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

logger = logging.getLogger(__name__)

admin_only = require_admin_role({"admin"})

router = APIRouter(
    prefix="/admin/flags",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.get("", response_model=list[FeatureFlagOut], summary="List feature flags")
async def list_flags(
    _: Annotated[Depends, Depends(admin_only)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> list[FeatureFlagOut]:
    await ensure_known_flags(db)
    res = await db.execute(select(FeatureFlag).order_by(FeatureFlag.key.asc()))
    items = list(res.scalars().all())
    return items


@router.patch("/{key}", response_model=FeatureFlagOut, summary="Update feature flag")
async def update_flag(
    key: str,
    body: FeatureFlagUpdateIn,
    request: Request,
    current: Annotated[Any, Depends(admin_only)],
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> FeatureFlagOut:
    if body.value is None and body.description is None and body.audience is None:
        msg = "Either 'value', 'description' or 'audience' must be provided"
        logger.warning("Feature flag %s update rejected: %s", key, msg)
        raise HTTPException(status_code=400, detail=msg)

    before = await db.get(FeatureFlag, key)
    before_dump = (
        {
            "key": before.key,
            "value": bool(before.value),
            "description": before.description,
            "audience": before.audience,
        }
        if before
        else None
    )

    updated = await set_flag(
        db,
        key=key,
        value=body.value,
        description=body.description,
        updated_by=str(getattr(current, "id", "")) or None,
        audience=body.audience,
    )

    after_dump = {
        "key": updated.key,
        "value": bool(updated.value),
        "description": updated.description,
        "audience": updated.audience,
    }

    await audit_log(
        db,
        actor_id=str(getattr(current, "id", "")),
        action="feature_flag_update",
        resource_type="feature_flag",
        resource_id=key,
        before=before_dump,
        after=after_dump,
        request=request,
    )

    invalidate_cache()
    invalidate_menu_cache()

    return updated
