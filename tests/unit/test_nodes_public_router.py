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
from app.core.preview import PreviewContext  # noqa: E402
from app.domains.navigation.api.nodes_public_router import (
    router as public_router,  # noqa: E402
)
from app.domains.quests.infrastructure.models.navigation_cache_models import (  # noqa: E402
    NavigationCache,
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
        await conn.run_sync(NavigationCache.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    app = FastAPI()
    app.include_router(public_router)

    async def override_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[api_deps.get_current_user_optional] = lambda: None
    app.dependency_overrides[api_deps.get_preview_context] = lambda: PreviewContext()

    return app, async_session


@pytest.mark.asyncio
async def test_get_next_nodes_respects_access(app_and_session):
    app, async_session = app_and_session
    async with async_session() as session:
        ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=uuid.uuid4())
        session.add(ws)
        await session.commit()
        public = Node(
            id=uuid.uuid4(),
            workspace_id=ws.id,
            slug="pub",
            title="Pub",
            content={},
            media=[],
            author_id=uuid.uuid4(),
            is_visible=True,
            is_public=True,
            premium_only=False,
            is_recommendable=True,
        )
        private = Node(
            id=uuid.uuid4(),
            workspace_id=ws.id,
            slug="priv",
            title="Priv",
            content={},
            media=[],
            author_id=uuid.uuid4(),
            is_visible=True,
            is_public=False,
            premium_only=False,
            is_recommendable=True,
        )
        premium = Node(
            id=uuid.uuid4(),
            workspace_id=ws.id,
            slug="prem",
            title="Prem",
            content={},
            media=[],
            author_id=uuid.uuid4(),
            is_visible=True,
            is_public=True,
            premium_only=True,
            is_recommendable=True,
        )
        session.add_all([public, private, premium])
        await session.commit()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp_ok = await ac.get(f"/nodes/{public.slug}/next")
    assert resp_ok.status_code == 200
    assert resp_ok.json()["mode"] == "auto"

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp_err = await ac.get(f"/nodes/{private.slug}/next")
    assert resp_err.status_code == 404

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp_premium = await ac.get(f"/nodes/{premium.slug}/next")
    assert resp_premium.status_code == 200
    assert resp_premium.json()["mode"] == "auto"


@pytest.mark.asyncio
async def test_get_next_modes_checks_visibility(app_and_session):
    app, async_session = app_and_session
    async with async_session() as session:
        ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=uuid.uuid4())
        session.add(ws)
        await session.commit()
        public = Node(
            id=uuid.uuid4(),
            workspace_id=ws.id,
            slug="pub",
            title="Pub",
            content={},
            media=[],
            author_id=uuid.uuid4(),
            is_visible=True,
            is_public=True,
            premium_only=False,
            is_recommendable=True,
        )
        private = Node(
            id=uuid.uuid4(),
            workspace_id=ws.id,
            slug="priv",
            title="Priv",
            content={},
            media=[],
            author_id=uuid.uuid4(),
            is_visible=True,
            is_public=False,
            premium_only=False,
            is_recommendable=True,
        )
        session.add_all([public, private])
        await session.commit()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp_ok = await ac.get(f"/nodes/{public.slug}/next_modes")
    assert resp_ok.status_code == 200
    assert resp_ok.json()["default_mode"] == "compass"

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp_err = await ac.get(f"/nodes/{private.slug}/next_modes")
    assert resp_err.status_code == 404
