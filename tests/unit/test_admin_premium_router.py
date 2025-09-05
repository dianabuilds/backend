import importlib
import sys

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Ensure app package resolves
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.api.admin_premium import admin_required, get_plan_service  # noqa: E402
from app.api.admin_premium import router as admin_premium_router  # noqa: E402
from app.domains.premium.application.subscription_plan_service import (  # noqa: E402
    SubscriptionPlanService,
)
from app.domains.premium.infrastructure.models.premium_models import (  # noqa: E402
    SubscriptionPlan,
    UserSubscription,
)
from app.domains.users.infrastructure.models.user import User  # noqa: E402
from app.providers.db.session import get_db  # noqa: E402


@pytest_asyncio.fixture()
async def app_and_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(SubscriptionPlan.__table__.create)
        await conn.run_sync(UserSubscription.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    app = FastAPI()
    app.include_router(admin_premium_router)

    async def override_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[admin_required] = lambda: None
    service = SubscriptionPlanService()
    app.dependency_overrides[get_plan_service] = lambda: service
    return app, async_session


@pytest.mark.asyncio
async def test_admin_premium_router_crud(app_and_session):
    app, _ = app_and_session
    transport = ASGITransport(app=app)
    payload = {"slug": "pro", "title": "Pro"}

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp_create = await ac.post("/admin/premium/plans", json=payload)
    assert resp_create.status_code == 200
    plan_id = resp_create.json()["id"]

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp_list = await ac.get("/admin/premium/plans")
    assert resp_list.status_code == 200
    assert len(resp_list.json()) == 1

    update_payload = {"slug": "pro", "title": "Pro Plus"}
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp_update = await ac.put(f"/admin/premium/plans/{plan_id}", json=update_payload)
    assert resp_update.status_code == 200
    assert resp_update.json()["title"] == "Pro Plus"

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp_delete = await ac.delete(f"/admin/premium/plans/{plan_id}")
    assert resp_delete.status_code == 200
    assert resp_delete.json()["status"] == "ok"

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp_final = await ac.get("/admin/premium/plans")
    assert resp_final.status_code == 200
    assert resp_final.json() == []
