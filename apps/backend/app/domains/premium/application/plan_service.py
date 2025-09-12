from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.kernel.preview import PreviewContext
from app.domains.premium.application.quota_service import QuotaService
from app.domains.premium.infrastructure.models.premium_models import SubscriptionPlan
from app.domains.premium.plans_impl import (
    build_quota_plans_map as _build_quota_plans_map,
)
from app.domains.premium.plans_impl import (
    get_active_plans as _get_active_plans,
)
from app.domains.premium.plans_impl import (
    get_effective_plan_slug as _get_effective_plan_slug,
)
from app.domains.premium.plans_impl import (
    get_plan_by_slug as _get_plan_by_slug,
)


async def get_active_plans(db: AsyncSession) -> list[SubscriptionPlan]:
    return await _get_active_plans(db)


async def get_plan_by_slug(db: AsyncSession, slug: str) -> SubscriptionPlan | None:
    return await _get_plan_by_slug(db, slug)


async def get_effective_plan_slug(
    db: AsyncSession, user_id: str | None, *, preview: PreviewContext | None = None
) -> str:
    return await _get_effective_plan_slug(db, user_id, preview=preview)


async def build_quota_plans_map(db: AsyncSession) -> dict[str, Any]:
    return await _build_quota_plans_map(db)


_qs: QuotaService | None = None


def _get_qs() -> QuotaService:
    global _qs
    if _qs is None:
        _qs = QuotaService()
    return _qs


async def refresh_quota_limits(db: AsyncSession) -> None:
    """Reload quota limits from plans without restarting the service."""
    plans = await _build_quota_plans_map(db)
    _get_qs().set_plans_map(plans)

