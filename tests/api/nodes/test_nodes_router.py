import importlib
import sys
import types
import uuid
from datetime import datetime

import pytest
import pytest_asyncio
import sqlalchemy as sa
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Ensure app package resolves
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.api import deps as api_deps  # noqa: E402
from app.core.preview import PreviewContext  # noqa: E402
from app.domains.navigation.api.nodes_public_router import router as nav_router  # noqa: E402
from app.domains.nodes.api.nodes_router import router as nodes_router  # noqa: E402
from app.domains.nodes.infrastructure.models.node import Node  # noqa: E402
from app.domains.nodes.models import NodeItem  # noqa: E402
from app.domains.quests.infrastructure.models.navigation_cache_models import (  # noqa: E402
    NavigationCache,
)
from app.providers.db.session import get_db  # noqa: E402
from app.schemas.nodes_common import Status, Visibility  # noqa: E402

# Minimal workspaces table for NodeItem foreign keys
workspace_stub = sa.Table(
    "workspaces",
    NodeItem.__table__.metadata,
    sa.Column("id", sa.Integer, primary_key=True),
)


@pytest_asyncio.fixture()
async def app_and_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        Workspace.__table__.c.id.type = sa.Integer()
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(workspace_stub.create)
        Node.__table__.c.id.type = sa.Integer()
        Node.__table__.c.account_id.type = sa.Integer()
        await conn.run_sync(Node.__table__.create)
        # SQLite adjustments
        NodeItem.__table__.c.id_bigint.type = sa.Integer()
        NodeItem.__table__.c.workspace_id.type = sa.Integer()
        await conn.run_sync(NodeItem.__table__.create)
        await conn.run_sync(NavigationCache.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    app = FastAPI()
    app.include_router(nodes_router)
    app.include_router(nodes_router, prefix="/accounts/{account_id}")
    app.include_router(nav_router)

    async def override_db():
        async with async_session() as session:
            yield session

    user = types.SimpleNamespace(id=uuid.uuid4(), role="user")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[api_deps.get_current_user] = lambda: user
    app.dependency_overrides[api_deps.get_current_user_optional] = lambda: None
    app.dependency_overrides[api_deps.get_preview_context] = lambda: PreviewContext()
    nodes_router.require_ws_guest = lambda account_id, user, db: None

    return app, async_session, user


@pytest.mark.asyncio
async def test_get_node_scoped_by_space(app_and_session):
    app, async_session, user = app_and_session
    async with async_session() as session:
        ws1 = Workspace(name="W1", slug="w1", owner_user_id=user.id)
        ws2 = Workspace(name="W2", slug="w2", owner_user_id=user.id)
        session.add_all([ws1, ws2])
        await session.flush()
        node = Node(
            account_id=ws1.id,
            slug="n1",
            title="Node1",
            content={},
            media=[],
            author_id=user.id,
            is_visible=True,
            is_public=True,
            premium_only=False,
            is_recommendable=True,
        )
        session.add(node)
        await session.execute(sa.insert(workspace_stub), [{"id": ws1.id}, {"id": ws2.id}])
        await session.commit()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp_ok = await ac.get(f"/accounts/{ws1.id}/nodes/{node.slug}")
    assert resp_ok.status_code == 200
    assert resp_ok.json()["slug"] == node.slug
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp_not_found = await ac.get(f"/accounts/{ws2.id}/nodes/{node.slug}")
    assert resp_not_found.status_code == 404


@pytest.mark.asyncio
async def test_list_nodes_sorted(app_and_session):
    app, async_session, user = app_and_session
    async with async_session() as session:
        ws = Workspace(name="W", slug="w", owner_user_id=user.id)
        session.add(ws)
        await session.flush()
        await session.execute(sa.insert(workspace_stub), [{"id": ws.id}])
        await session.commit()
        n1 = Node(
            account_id=ws.id,
            slug="n1",
            title="N1",
            content={},
            media=[],
            author_id=user.id,
            is_visible=True,
            is_public=True,
            views=5,
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 1),
            premium_only=False,
            is_recommendable=True,
        )
        n2 = Node(
            account_id=ws.id,
            slug="n2",
            title="N2",
            content={},
            media=[],
            author_id=user.id,
            is_visible=True,
            is_public=True,
            views=10,
            created_at=datetime(2024, 1, 2),
            updated_at=datetime(2024, 1, 3),
            premium_only=False,
            is_recommendable=True,
        )
        n3 = Node(
            account_id=ws.id,
            slug="n3",
            title="N3",
            content={},
            media=[],
            author_id=user.id,
            is_visible=True,
            is_public=True,
            views=0,
            created_at=datetime(2024, 1, 3),
            updated_at=datetime(2024, 1, 2),
            premium_only=False,
            is_recommendable=True,
        )
        session.add_all([n1, n2, n3])
        await session.commit()
        items = [
            NodeItem(
                id=1,
                node_id=n1.id,
                workspace_id=ws.id,
                type="node",
                slug=n1.slug,
                title=n1.title,
                status=Status.published,
                visibility=Visibility.public,
            ),
            NodeItem(
                id=2,
                node_id=n2.id,
                workspace_id=ws.id,
                type="node",
                slug=n2.slug,
                title=n2.title,
                status=Status.published,
                visibility=Visibility.public,
            ),
            NodeItem(
                id=3,
                node_id=n3.id,
                workspace_id=ws.id,
                type="node",
                slug=n3.slug,
                title=n3.title,
                status=Status.published,
                visibility=Visibility.public,
            ),
        ]
        session.add_all(items)
        await session.commit()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/accounts/{ws.id}/nodes", params={"sort": "created_desc"})
    assert [n["slug"] for n in resp.json()] == ["n3", "n2", "n1"]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/accounts/{ws.id}/nodes", params={"sort": "created_asc"})
    assert [n["slug"] for n in resp.json()] == ["n1", "n2", "n3"]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/accounts/{ws.id}/nodes", params={"sort": "views_desc"})
    assert [n["slug"] for n in resp.json()] == ["n2", "n1", "n3"]


@pytest.mark.asyncio
async def test_next_returns_fallback_for_empty_nav(app_and_session):
    app, async_session, user = app_and_session
    async with async_session() as session:
        ws = Workspace(name="W", slug="w", owner_user_id=user.id)
        session.add(ws)
        await session.flush()
        node = Node(
            account_id=ws.id,
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
        session.add_all([ws, node])
        await session.execute(sa.insert(workspace_stub), [{"id": ws.id}])
        session.add(NavigationCache(node_slug="n1", navigation={}, compass=[], echo=[]))
        await session.commit()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/nodes/{node.slug}/next")
    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "auto"
    assert body["transitions"] == []
