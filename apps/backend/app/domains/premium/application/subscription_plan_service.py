from __future__ import annotations  # mypy: ignore-errors

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.premium.infrastructure.models.premium_models import SubscriptionPlan
from app.schemas.premium import SubscriptionPlanIn


class SubscriptionPlanService:
    async def list_plans(self, db: AsyncSession) -> list[SubscriptionPlan]:
        res = await db.execute(select(SubscriptionPlan).order_by(SubscriptionPlan.order.asc()))
        return list(res.scalars().all())

    async def create_plan(self, db: AsyncSession, payload: SubscriptionPlanIn) -> SubscriptionPlan:
        plan = SubscriptionPlan(**payload.model_dump())
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        return plan

    async def update_plan(
        self, db: AsyncSession, plan_id: UUID, payload: SubscriptionPlanIn
    ) -> SubscriptionPlan:
        plan = await db.get(SubscriptionPlan, plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        for key, value in payload.model_dump().items():
            setattr(plan, key, value)
        await db.commit()
        await db.refresh(plan)
        return plan

    async def delete_plan(self, db: AsyncSession, plan_id: UUID) -> None:
        plan = await db.get(SubscriptionPlan, plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        await db.delete(plan)
        await db.commit()
