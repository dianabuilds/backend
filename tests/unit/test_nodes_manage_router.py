import importlib
import sys
import types
import uuid
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Ensure app package resolves
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.core.db.session import get_db  # noqa: E402
from app.api import deps as api_deps  # noqa: E402
from app.core import workspace_context as ws_ctx  # noqa: E402
from app.domains.navigation.api.nodes_manage_router import (
    router as manage_router,  # noqa: E402
)
from app.domains.navigation.infrastructure.models.transition_models import (  # noqa: E402
    NodeTransition,
)
from app.domains.nodes.infrastructure.models.node import Node  # noqa: E402
from app.domains.workspaces.infrastructure.models import Workspace  # noqa: E402
from app.domains.tags.models import Tag  # noqa: E402
from app.domains.tags.infrastructure.models.tag_models import NodeTag  # noqa: E402


@pytest_asyncio.fixture()
async def app_and_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(Tag.__table__.create)
        await conn.run_sync(Node.__table__.create)
        await conn.run_sync(NodeTag.__table__.create)
        await conn.run_sync(NodeTransition.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    app = FastAPI()
    app.include_router(manage_router)

    async def override_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db

    user = types.SimpleNamespace(id=uuid.uuid4(), is_premium=False, role="user")

    async def override_user():
        return user

    app.dependency_overrides[api_deps.get_current_user] = override_user
    app.dependency_overrides[ws_ctx.require_workspace] = lambda: None

    return app, async_session, user


@pytest.mark.asyncio
async def test_create_transition_success_and_missing_target(app_and_session):
    app, async_session, user = app_and_session
    async with async_session() as session:
        ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user.id)
        session.add(ws)
        await session.commit()
        n1 = Node(
            alt_id=uuid.uuid4(),
            workspace_id=ws.id,
            slug="a",
            title="A",
            content={},
            media=[],
            author_id=user.id,
            is_visible=True,
            is_public=True,
            premium_only=False,
            is_recommendable=True,
        )
        n2 = Node(
            alt_id=uuid.uuid4(),
            workspace_id=ws.id,
            slug="b",
            title="B",
            content={},
            media=[],
            author_id=uuid.uuid4(),
            is_visible=True,
            is_public=True,
            premium_only=False,
            is_recommendable=True,
        )
        session.add_all([n1, n2])
        await session.commit()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            f"/nodes/{n1.slug}/transitions",
            params={"workspace_id": str(ws.id)},
            json={"to_slug": n2.slug},
        )
    assert resp.status_code == 200
    assert "id" in resp.json()

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            f"/nodes/{n1.slug}/transitions",
            params={"workspace_id": str(ws.id)},
            json={"to_slug": "missing"},
        )
    assert resp.status_code == 404
