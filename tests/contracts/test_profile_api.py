from __future__ import annotations

import types
import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.api import deps as api_deps
from app.domains.users.api.routers import router as users_router
from app.domains.users.infrastructure.models.user import User
from app.domains.users.infrastructure.models.user_profile import UserProfile
from app.providers.db.session import get_db


@pytest.mark.asyncio
async def test_profile_settings_contract() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(UserProfile.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    user = types.SimpleNamespace(id=uuid.uuid4(), role="user", is_active=True)

    app = FastAPI()
    app.include_router(users_router)

    async def override_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[api_deps.get_current_user] = lambda: user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/users/me/profile")
        assert resp.status_code == 200
        assert resp.json() == {"timezone": None, "locale": None, "links": {}}

        resp = await ac.patch("/users/me/settings", json={"preferences": {"theme": "dark"}})
        assert resp.status_code == 200
        assert resp.json() == {"preferences": {"theme": "dark"}}

        resp = await ac.patch("/users/me/settings", json={"preferences": {"lang": "ru"}})
        assert resp.status_code == 200
        assert resp.json() == {"preferences": {"theme": "dark", "lang": "ru"}}
