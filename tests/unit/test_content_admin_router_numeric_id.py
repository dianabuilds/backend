from __future__ import annotations

import importlib
import sys
import types
import uuid

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

from app.domains.nodes.content_admin_router import router as admin_router  # noqa: E402
from app.domains.nodes.infrastructure.models.node import Node  # noqa: E402
from app.domains.nodes.models import NodeItem, NodePatch  # noqa: E402
from app.domains.quests.infrastructure.models import quest_models  # noqa: F401, E402
from app.domains.quests.infrastructure.models.navigation_cache_models import (  # noqa: E402
    NavigationCache,
)
from app.domains.tags.infrastructure.models.tag_models import NodeTag  # noqa: E402
from app.domains.tags.models import Tag  # noqa: E402
from app.domains.workspaces.infrastructure.models import Workspace  # noqa: E402
from app.providers.db.session import get_db  # noqa: E402
from app.security import auth_user, require_ws_editor  # noqa: E402


@pytest_asyncio.fixture()
async def app_client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(Tag.__table__.create)
        await conn.run_sync(Node.__table__.create)
        await conn.run_sync(NodeTag.__table__.create)
        NodeItem.__table__.c.id_bigint.type = sa.Integer()
        await conn.run_sync(NodeItem.__table__.create)
        await conn.run_sync(NodePatch.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    app = FastAPI()
    app.include_router(admin_router)

    async def override_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db

    user = types.SimpleNamespace(id=uuid.uuid4())
    app.dependency_overrides[auth_user] = lambda: user
    app.dependency_overrides[require_ws_editor] = lambda: None

    async with async_session() as session:
        ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user.id)
        session.add(ws)
        node = Node(
            id=1,
            account_id=ws.id,
            slug="n1",
            title="N1",
            content={},
            author_id=user.id,
        )
        item = NodeItem(
            id=2,
            node_id=node.id,
            workspace_id=ws.id,
            type="quest",
            slug="n1",
            title="N1",
        )
        session.add_all([node, item])
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, ws.id, item.id, node.id


@pytest_asyncio.fixture()
async def app_client_with_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(Tag.__table__.create)
        await conn.run_sync(Node.__table__.create)
        await conn.run_sync(NodeTag.__table__.create)
        NodeItem.__table__.c.id_bigint.type = sa.Integer()
        NodeItem.__table__.c.id_bigint.type = sa.Integer()
        await conn.run_sync(NodeItem.__table__.create)
        await conn.run_sync(NodePatch.__table__.create)
        await conn.run_sync(NavigationCache.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    app = FastAPI()
    app.include_router(admin_router)

    async def override_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db

    user = types.SimpleNamespace(id=uuid.uuid4())
    app.dependency_overrides[auth_user] = lambda: user
    app.dependency_overrides[require_ws_editor] = lambda: None

    async with async_session() as session:
        ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user.id)
        session.add(ws)
        node = Node(
            id=1,
            account_id=ws.id,
            slug="n1",
            title="N1",
            content={},
            author_id=user.id,
        )
        item = NodeItem(
            id=2,
            node_id=node.id,
            workspace_id=ws.id,
            type="quest",
            slug="n1",
            title="N1",
        )
        session.add_all([node, item])
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, ws.id, item.id, node.id, async_session


@pytest.mark.asyncio
async def test_get_node_by_id(app_client):
    client, acc_id, item_id, node_id = app_client
    resp = await client.get(f"/admin/accounts/{acc_id}/nodes/{item_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == node_id
    assert data["contentId"] == item_id
    assert data["nodeId"] == node_id


@pytest.mark.asyncio
async def test_put_node_by_id_updates(app_client_with_session):
    client, acc_id, item_id, node_id, async_session = app_client_with_session
    resp = await client.put(f"/admin/accounts/{acc_id}/nodes/{item_id}", json={"title": "N2"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == node_id
    assert data["title"] == "N2"
    async with async_session() as session:
        node = await session.get(Node, node_id)
        item = await session.get(NodeItem, item_id)
        assert node.title == "N2"
        assert item.title == "N2"


@pytest_asyncio.fixture()
async def app_client_node_only():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(Tag.__table__.create)
        await conn.run_sync(Node.__table__.create)
        await conn.run_sync(NodeTag.__table__.create)
        NodeItem.__table__.c.id_bigint.type = sa.Integer()
        NodeItem.__table__.c.id_bigint.type = sa.Integer()
        await conn.run_sync(NodeItem.__table__.create)
        await conn.run_sync(NodePatch.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    app = FastAPI()
    app.include_router(admin_router)

    async def override_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db

    user = types.SimpleNamespace(id=uuid.uuid4())
    app.dependency_overrides[auth_user] = lambda: user
    app.dependency_overrides[require_ws_editor] = lambda: None

    async with async_session() as session:
        ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user.id)
        session.add(ws)
        node = Node(
            id=1,
            account_id=ws.id,
            slug="n2",
            title="N2",
            content={},
            author_id=user.id,
        )
        session.add(node)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, ws.id, node.id, async_session


@pytest.mark.asyncio
async def test_get_node_auto_creates_item(app_client_node_only):
    client, acc_id, node_id, async_session = app_client_node_only
    resp = await client.get(f"/admin/accounts/{acc_id}/nodes/{node_id}")
    assert resp.status_code == 200
    async with async_session() as session:
        res = await session.execute(sa.select(NodeItem).where(NodeItem.node_id == node_id))
        assert res.scalar_one() is not None
