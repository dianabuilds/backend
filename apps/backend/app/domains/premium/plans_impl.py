from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.domains.premium.infrastructure.models.premium_models import SubscriptionPlan, UserSubscription
from app.core.preview import PreviewContext


async def get_active_plans(db: AsyncSession) -> List[SubscriptionPlan]:
    res = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.is_active == True).order_by(SubscriptionPlan.order.asc())  # noqa: E712
    )
    return list(res.scalars().all())


async def get_plan_by_slug(db: AsyncSession, slug: str) -> Optional[SubscriptionPlan]:
    res = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.slug == slug))
    return res.scalars().first()


async def get_effective_plan_slug(
    db: AsyncSession, user_id: str | None, *, preview: PreviewContext | None = None
) -> str:
    if not user_id:
        return "free"
    now = (
        preview.now.astimezone(timezone.utc)
        if preview and preview.now
        else datetime.now(tz=timezone.utc)
    )
    res = await db.execute(
        select(UserSubscription, SubscriptionPlan)
        .join(SubscriptionPlan, UserSubscription.plan_id == SubscriptionPlan.id)
        .where(
            UserSubscription.user_id == user_id,
            UserSubscription.status == "active",
            (UserSubscription.ends_at == None) | (UserSubscription.ends_at > now),  # noqa: E711
            SubscriptionPlan.is_active == True,  # noqa: E712
        )
        .order_by(UserSubscription.started_at.desc())
    )
    row = res.first()
    if row and row[1] and row[1].slug:
        return row[1].slug
    return "free"


async def build_quota_plans_map(db: AsyncSession) -> Dict[str, Any]:
    plans = await get_active_plans(db)
    out: Dict[str, Any] = {}
    for p in plans:
        limits = p.monthly_limits or {}
        conf: Dict[str, Any] = {"__grace__": 0}
        for k, v in limits.items():
            try:
                limit_val = int(v)
            except Exception:
                continue
            conf[k] = {"month": limit_val}
        out[p.slug] = conf
    out.setdefault("free", {"__grace__": 0})
    return out
