from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.preview import PreviewContext
from app.domains.premium.infrastructure.models.premium_models import (
    SubscriptionPlan,
    UserSubscription,
)


async def get_active_plans(db: AsyncSession) -> list[SubscriptionPlan]:
    res = await db.execute(
        select(SubscriptionPlan)
        .where(SubscriptionPlan.is_active.is_(True))
        .order_by(SubscriptionPlan.order.asc())
    )
    return list(res.scalars().all())


async def get_plan_by_slug(db: AsyncSession, slug: str) -> SubscriptionPlan | None:
    res = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.slug == slug)
    )
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
            (UserSubscription.ends_at.is_(None)) | (UserSubscription.ends_at > now),
            SubscriptionPlan.is_active.is_(True),
        )
        .order_by(UserSubscription.started_at.desc())
    )
    row = res.first()
    if row and row[1] and row[1].slug:
        return row[1].slug
    return "free"


async def build_quota_plans_map(db: AsyncSession) -> dict[str, Any]:
    plans = await get_active_plans(db)
    out: dict[str, Any] = {}
    for p in plans:
        limits = p.monthly_limits or {}
        conf: dict[str, Any] = {"__grace__": 0}
        for k, v in limits.items():
            try:
                limit_val = int(v)
            except Exception:
                continue
            conf[k] = {"month": limit_val}
        out[p.slug] = conf
    out.setdefault("free", {"__grace__": 0})
    return out
