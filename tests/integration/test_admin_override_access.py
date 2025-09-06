from __future__ import annotations

import types
import uuid

import pytest
import pytest_asyncio
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.api.admin_override import register_admin_override
from app.api.deps import get_current_user, get_db
from app.domains.admin.application.feature_flag_service import (
    FeatureFlagKey,
    ensure_known_flags,
    set_flag,
)
from app.domains.admin.infrastructure.models.feature_flag import FeatureFlag
from app.domains.nodes.policies.node_policy import NodePolicy


@pytest_asyncio.fixture()
async def client_fixture():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(FeatureFlag.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    app = FastAPI()
    register_admin_override(app)

    async def override_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db

    user = types.SimpleNamespace(id=uuid.uuid4(), role="editor")
    app.dependency_overrides[get_current_user] = lambda: user

    @app.get("/node")
    async def get_node(request: Request, current_user: object = user) -> dict:
        node = types.SimpleNamespace(author_id=uuid.uuid4(), is_visible=False)
        NodePolicy.ensure_can_view(
            node,
            current_user,
            override=bool(getattr(request.state, "admin_override", False)),
        )
        return {"ok": True}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, async_session


@pytest.mark.asyncio
async def test_access_denied_without_override(client_fixture):
    client, session_factory = client_fixture
    async with session_factory() as session:
        await ensure_known_flags(session)
        await session.commit()
    resp = await client.get("/node")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_access_allowed_with_override(client_fixture):
    client, session_factory = client_fixture
    async with session_factory() as session:
        await ensure_known_flags(session)
        await set_flag(session, FeatureFlagKey.ADMIN_OVERRIDE, True)
        await session.commit()
    resp = await client.get(
        "/node",
        headers={"X-Admin-Override": "on", "X-Override-Reason": "test"},
    )
    assert resp.status_code == 200
