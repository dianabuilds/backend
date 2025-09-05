import importlib
import sys

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Ensure app package resolves
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.domains.premium.application.subscription_plan_service import (  # noqa: E402
    SubscriptionPlanService,
)
from app.domains.premium.infrastructure.models.premium_models import (  # noqa: E402
    SubscriptionPlan,
    UserSubscription,
)
from app.domains.users.infrastructure.models.user import User  # noqa: E402
from app.schemas.premium import SubscriptionPlanIn  # noqa: E402


@pytest.mark.asyncio
async def test_subscription_plan_service_crud():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(SubscriptionPlan.__table__.create)
        await conn.run_sync(UserSubscription.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    service = SubscriptionPlanService()
    async with async_session() as session:
        created = await service.create_plan(
            session,
            SubscriptionPlanIn(slug="basic", title="Basic"),
        )
        plans = await service.list_plans(session)
        assert len(plans) == 1
        assert plans[0].slug == "basic"

        updated = await service.update_plan(
            session,
            created.id,
            SubscriptionPlanIn(slug="basic", title="Updated"),
        )
        assert updated.title == "Updated"

        await service.delete_plan(session, created.id)
        plans_after = await service.list_plans(session)
        assert plans_after == []

    # ensure deleting nonexistent plan raises
    async with async_session() as session:
        with pytest.raises(HTTPException):
            await service.delete_plan(session, created.id)
