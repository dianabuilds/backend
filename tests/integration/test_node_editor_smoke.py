from __future__ import annotations

import os
import types
import uuid

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("TESTING", "true")

from app.domains.nodes.api import admin_nodes_router
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.models import NodeItem, NodePatch
from app.domains.tags.infrastructure.models.tag_models import NodeTag
from app.domains.tags.models import Tag
from app.domains.workspaces.infrastructure.models import Workspace
from app.providers.db.session import get_db


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
    app.include_router(admin_nodes_router.router)

    async def override_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db

    user = types.SimpleNamespace(id=uuid.uuid4())
    app.dependency_overrides[admin_nodes_router.admin_required] = lambda: user

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
            created_by_user_id=user.id,
        )
        session.add_all([ws, node, item])
        await session.commit()
        ws_id = ws.id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, ws_id


@pytest.mark.asyncio
async def test_open_node_from_list(app_client):
    client, ws_id = app_client
    resp = await client.get(f"/admin/workspaces/{ws_id}/nodes")
    assert resp.status_code == 200
    node_id = resp.json()[0]["id"]
    resp2 = await client.get(f"/admin/workspaces/{ws_id}/nodes/{node_id}")
    assert resp2.status_code == 200
