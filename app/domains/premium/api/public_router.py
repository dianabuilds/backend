from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.domains.users.infrastructure.models.user import User
from app.domains.premium.quotas import get_quota_status
from app.domains.premium.plans import get_effective_plan_slug

router = APIRouter(prefix="/premium", tags=["premium"])


@router.get("/me/limits")
async def my_limits(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    plan = await get_effective_plan_slug(db, str(user.id))
    stories = await get_quota_status(db, user.id, quota_key="stories", scope="month")
    return {"plan": plan, "limits": {"stories": {"month": stories}}}
