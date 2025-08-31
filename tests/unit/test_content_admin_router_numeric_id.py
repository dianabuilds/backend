from __future__ import annotations

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
from app.domains.nodes.content_admin_router import router as admin_router  # noqa: E402
from app.domains.nodes.infrastructure.models.node import Node  # noqa: E402
from app.domains.nodes.models import NodeItem, NodePatch  # noqa: E402
from app.domains.tags.infrastructure.models.tag_models import NodeTag  # noqa: E402
from app.domains.tags.models import Tag  # noqa: E402
from app.domains.workspaces.infrastructure.models import Workspace  # noqa: E402
from app.security import auth_user, require_ws_editor  # noqa: E402


@pytest_asyncio.fixture()
async def app_client():
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
            alt_id=uuid.uuid4(),
            workspace_id=ws.id,
            slug="n1",
            title="N1",
            content={},
            author_id=user.id,
        )
        item = NodeItem(
            id=uuid.uuid4(),
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
        yield client, ws.id, node.id, item.id


@pytest.mark.asyncio
async def test_get_node_by_numeric_id(app_client):
    client, ws_id, node_id, item_id = app_client
    resp = await client.get(f"/admin/workspaces/{ws_id}/nodes/{node_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(item_id)


@pytest_asyncio.fixture()
async def app_client_node_only():
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
            workspace_id=ws.id,
            slug="n2",
            title="N2",
            content={},
            author_id=user.id,
        )
        session.add(node)
        await session.commit()
        node_alt = node.alt_id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, ws.id, node.id, node_alt, async_session


@pytest.mark.asyncio
async def test_get_node_creates_item_if_missing(app_client_node_only):
    client, ws_id, node_id, node_alt, async_session = app_client_node_only
    resp = await client.get(f"/admin/workspaces/{ws_id}/nodes/{node_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(node_alt)
    async with async_session() as session:
        item = await session.get(NodeItem, node_alt)
        assert item is not None
        assert item.node_id == node_id
