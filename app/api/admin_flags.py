from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.feature_flag import FeatureFlag
from app.schemas.flags import FeatureFlagOut, FeatureFlagUpdateIn
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role
from app.services.feature_flags import set_flag, invalidate_cache
from app.services.audit import audit_log
from app.services.admin_menu import invalidate_menu_cache

admin_only = require_admin_role({"admin"})

router = APIRouter(
    prefix="/admin/flags",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.get("", response_model=list[FeatureFlagOut], summary="List feature flags")
async def list_flags(
    _: Depends = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
) -> List[FeatureFlagOut]:
    res = await db.execute(select(FeatureFlag).order_by(FeatureFlag.key.asc()))
    items = list(res.scalars().all())
    return items


@router.patch("/{key}", response_model=FeatureFlagOut, summary="Update feature flag")
async def update_flag(
    key: str,
    body: FeatureFlagUpdateIn,
    request: Request,
    current = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
) -> FeatureFlagOut:
    before = await db.get(FeatureFlag, key)
    before_dump = {
        "key": before.key,
        "value": bool(before.value),
        "description": before.description,
    } if before else None

    updated = await set_flag(
        db,
        key=key,
        value=body.value,
        description=body.description,
        updated_by=str(getattr(current, "id", "")) or None,
    )

    after_dump = {
        "key": updated.key,
        "value": bool(updated.value),
        "description": updated.description,
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
