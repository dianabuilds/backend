from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.premium.plans_impl import (
    get_active_plans as _get_active_plans,
    get_plan_by_slug as _get_plan_by_slug,
    get_effective_plan_slug as _get_effective_plan_slug,
    build_quota_plans_map as _build_quota_plans_map,
)
from app.domains.premium.infrastructure.models.premium_models import SubscriptionPlan


async def get_active_plans(db: AsyncSession) -> List[SubscriptionPlan]:
    return await _get_active_plans(db)


async def get_plan_by_slug(db: AsyncSession, slug: str) -> Optional[SubscriptionPlan]:
    return await _get_plan_by_slug(db, slug)


async def get_effective_plan_slug(db: AsyncSession, user_id: str | None) -> str:
    return await _get_effective_plan_slug(db, user_id)


async def build_quota_plans_map(db: AsyncSession) -> Dict[str, Any]:
    return await _build_quota_plans_map(db)
