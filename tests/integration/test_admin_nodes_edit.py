from __future__ import annotations

import types
import uuid

import pytest
import pytest_asyncio
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.db.session import get_db
from app.domains.nodes.api import admin_nodes_global_router
from app.domains.nodes.content_admin_router import (
    auth_user,
    require_ws_editor,
)
from app.domains.nodes.content_admin_router import (
    router as ws_router,
)
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.models import NodeItem, NodePatch
from app.domains.tags.infrastructure.models.tag_models import NodeTag
from app.domains.tags.models import Tag
from app.domains.workspaces.infrastructure.models import Workspace


@pytest_asyncio.fixture()
async def workspace_admin_client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(Tag.__table__.create)
        await conn.run_sync(Node.__table__.create)
        await conn.run_sync(NodeTag.__table__.create)
        await conn.run_sync(NodeItem.__table__.create)
        await conn.run_sync(NodePatch.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    app = FastAPI()
    app.include_router(ws_router)

    async def override_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db

    user = types.SimpleNamespace(id=uuid.uuid4())
    app.dependency_overrides[auth_user] = lambda: user
    app.dependency_overrides[require_ws_editor] = lambda: None

    async with async_session() as session:
        ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user.id)
        node = Node(
            id=1,
            workspace_id=ws.id,
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
        session.add_all([ws, node, item])
        await session.commit()
        ws_id, item_id, node_id = ws.id, item.id, node.id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, async_session, ws_id, item_id, node_id


@pytest_asyncio.fixture()
async def global_admin_client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        Node.__table__.c.workspace_id.nullable = True
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(Tag.__table__.create)
        await conn.run_sync(Node.__table__.create)
        await conn.run_sync(NodeTag.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    app = FastAPI()
    app.include_router(admin_nodes_global_router.router)

    async def override_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db

    user = types.SimpleNamespace(id=uuid.uuid4())
    app.dependency_overrides[admin_nodes_global_router.admin_required] = lambda: user

    async with async_session() as session:
        node = Node(
            id=1,
            slug="n1",
            title="N1",
            content={},
            media=[],
            author_id=user.id,
        )
        session.add(node)
        await session.commit()
        node_id = node.id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, async_session, node_id


@pytest_asyncio.fixture()
async def forbidden_global_client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        Node.__table__.c.workspace_id.nullable = True
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(Tag.__table__.create)
        await conn.run_sync(Node.__table__.create)
        await conn.run_sync(NodeTag.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    app = FastAPI()
    app.include_router(admin_nodes_global_router.router)

    async def override_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db

    async def forbidden_dep():
        raise HTTPException(status_code=403)

    app.dependency_overrides[admin_nodes_global_router.admin_required] = forbidden_dep

    async with async_session() as session:
        node = Node(
            id=1,
            slug="n1",
            title="N1",
            content={},
            media=[],
            author_id=uuid.uuid4(),
        )
        session.add(node)
        await session.commit()
        node_id = node.id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, node_id


@pytest.mark.asyncio
async def test_workspace_node_load_and_edit(workspace_admin_client):
    client, session_factory, ws_id, item_id, node_id = workspace_admin_client
    resp = await client.get(f"/admin/workspaces/{ws_id}/nodes/{item_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == node_id

    resp = await client.put(
        f"/admin/workspaces/{ws_id}/nodes/{item_id}", json={"title": "Updated"}
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"

    async with session_factory() as session:
        db_node = await session.get(Node, node_id)
        db_item = await session.get(NodeItem, item_id)
        assert db_node.title == "Updated"
        assert db_item.title == "Updated"


@pytest.mark.asyncio
async def test_global_node_load_and_edit(global_admin_client):
    client, session_factory, node_id = global_admin_client
    resp = await client.get(f"/admin/nodes/{node_id}")
    assert resp.status_code == 200

    resp = await client.put(f"/admin/nodes/{node_id}", json={"title": "NX"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "NX"

    async with session_factory() as session:
        db_node = await session.get(Node, node_id)
        assert db_node.title == "NX"


@pytest.mark.asyncio
async def test_global_node_forbidden(forbidden_global_client):
    client, node_id = forbidden_global_client
    resp = await client.get(f"/admin/nodes/{node_id}")
    assert resp.status_code == 403
