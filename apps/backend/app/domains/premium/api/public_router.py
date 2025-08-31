from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_preview_context
from app.core.db.session import get_db
from app.core.preview import PreviewContext
from app.domains.premium.plans import get_effective_plan_slug
from app.domains.premium.quotas import get_quota_status
from app.domains.users.infrastructure.models.user import User

router = APIRouter(prefix="/premium", tags=["premium"])


@router.get("/me/limits")
async def my_limits(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    preview: PreviewContext = Depends(get_preview_context),
) -> dict[str, Any]:
    plan = await get_effective_plan_slug(db, str(user.id), preview=preview)
    stories = await get_quota_status(
        db, user.id, quota_key="stories", scope="month", preview=preview
    )
    return {"plan": plan, "limits": {"stories": {"month": stories}}}
