import types
import uuid

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.db.session import get_db
from app.api import deps as api_deps
from app.core.workspace_context import require_workspace
from app.security import require_ws_viewer
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.api.nodes_router import router as nodes_router
from app.domains.quests.infrastructure.models.navigation_cache_models import NavigationCache
from app.domains.workspaces.infrastructure.models import Workspace


@pytest.mark.asyncio
async def test_update_node_invalidates_navigation_cache(monkeypatch) -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(Node.__table__.create)
        await conn.run_sync(NavigationCache.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    user = types.SimpleNamespace(id=uuid.uuid4(), role="admin")

    app = FastAPI()
    app.include_router(nodes_router)

    async def override_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[api_deps.get_current_user] = lambda: user
    app.dependency_overrides[require_workspace] = lambda **_: None
    app.dependency_overrides[require_ws_viewer] = lambda **_: None

    class DummyBus:
        async def publish(self, *args, **kwargs):
            return None

    from app.domains.system import events as event_mod

    monkeypatch.setattr(event_mod, "get_event_bus", lambda: DummyBus())

    async with async_session() as session:
        ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user.id)
        node = Node(
            id=uuid.uuid4(),
            workspace_id=ws.id,
            slug="n1",
            title="N1",
            content={},
            media=[],
            author_id=user.id,
            is_visible=True,
            is_public=True,
            premium_only=False,
            is_recommendable=True,
        )
        session.add_all(
            [
                ws,
                node,
                NavigationCache(node_slug="n1", navigation={"mode": "auto", "transitions": []}, compass=[], echo=[]),
            ]
        )
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.patch(
            f"/nodes/n1", params={"workspace_id": str(ws.id)}, json={"is_visible": False}
        )
        assert resp.status_code == 200

    async with async_session() as session:
        res = await session.execute(
            select(NavigationCache).where(NavigationCache.node_slug == "n1")
        )
        assert res.scalar_one_or_none() is None
