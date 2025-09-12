from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.premium.application.subscription_plan_service import (
    SubscriptionPlanService,
)
from app.domains.premium.infrastructure.models.premium_models import SubscriptionPlan
from app.kernel.db import get_db
from app.schemas.premium import SubscriptionPlanIn, SubscriptionPlanOut
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

admin_required = require_admin_role()

router = APIRouter(
    prefix="/admin/premium",
    tags=["admin"],
    dependencies=[Depends(admin_required)],
    responses=ADMIN_AUTH_RESPONSES,
)


def get_plan_service() -> SubscriptionPlanService:
    return SubscriptionPlanService()


@router.get(
    "/plans",
    response_model=list[SubscriptionPlanOut],
    summary="List subscription plans",
)
async def list_plans(
    db: Annotated[AsyncSession, Depends(get_db)],
    service: Annotated[SubscriptionPlanService, Depends(get_plan_service)],
) -> list[SubscriptionPlan]:
    return await service.list_plans(db)


@router.post("/plans", response_model=SubscriptionPlanOut, summary="Create subscription plan")
async def create_plan(
    payload: SubscriptionPlanIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    service: Annotated[SubscriptionPlanService, Depends(get_plan_service)],
) -> SubscriptionPlan:
    return await service.create_plan(db, payload)


@router.put(
    "/plans/{plan_id}",
    response_model=SubscriptionPlanOut,
    summary="Update subscription plan",
)
async def update_plan(
    plan_id: UUID,
    payload: SubscriptionPlanIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    service: Annotated[SubscriptionPlanService, Depends(get_plan_service)],
) -> SubscriptionPlan:
    return await service.update_plan(db, plan_id, payload)


@router.delete("/plans/{plan_id}", summary="Delete subscription plan")
async def delete_plan(
    plan_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    service: Annotated[SubscriptionPlanService, Depends(get_plan_service)],
) -> dict:
    await service.delete_plan(db, plan_id)
    return {"status": "ok"}

__all__ = [
    "router",
    "admin_required",
    "get_plan_service",
]


