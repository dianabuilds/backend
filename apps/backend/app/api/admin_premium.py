from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.db.session import get_db
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role
from app.domains.premium.infrastructure.models.premium_models import SubscriptionPlan
from app.schemas.premium import SubscriptionPlanIn, SubscriptionPlanOut

admin_required = require_admin_role()

router = APIRouter(
    prefix="/admin/premium",
    tags=["admin"],
    dependencies=[Depends(admin_required)],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.get("/plans", response_model=List[SubscriptionPlanOut], summary="List subscription plans")
async def list_plans(db: AsyncSession = Depends(get_db)) -> List[SubscriptionPlan]:
    res = await db.execute(select(SubscriptionPlan).order_by(SubscriptionPlan.order.asc()))
    return list(res.scalars().all())


@router.post("/plans", response_model=SubscriptionPlanOut, summary="Create subscription plan")
async def create_plan(payload: SubscriptionPlanIn, db: AsyncSession = Depends(get_db)) -> SubscriptionPlan:
    plan = SubscriptionPlan(**payload.model_dump())
    db.add(plan)
    await db.commit()
    return plan


@router.put("/plans/{plan_id}", response_model=SubscriptionPlanOut, summary="Update subscription plan")
async def update_plan(
    plan_id: UUID, payload: SubscriptionPlanIn, db: AsyncSession = Depends(get_db)
) -> SubscriptionPlan:
    plan = await db.get(SubscriptionPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    for k, v in payload.model_dump().items():
        setattr(plan, k, v)
    await db.commit()
    return plan


@router.delete("/plans/{plan_id}", summary="Delete subscription plan")
async def delete_plan(plan_id: UUID, db: AsyncSession = Depends(get_db)) -> dict:
    plan = await db.get(SubscriptionPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    await db.delete(plan)
    await db.commit()
    return {"status": "ok"}
