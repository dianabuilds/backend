from __future__ import annotations

import sys
import types
import uuid
from datetime import datetime

import pytest
import pytest_asyncio
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.db.session import get_db

_editorjs = types.ModuleType("editorjs_renderer")
_editorjs.collect_unknown_blocks = lambda *a, **k: []
_editorjs.render_html = lambda *a, **k: ""
sys.modules.setdefault("app.domains.nodes.application.editorjs_renderer", _editorjs)

from app.domains.nodes.api import admin_nodes_router
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.models import NodeItem, NodePublishJob
from app.domains.workspaces.infrastructure.models import Workspace


@pytest_asyncio.fixture()
async def admin_client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(Node.__table__.create)
        await conn.run_sync(NodeItem.__table__.create)
        NodePublishJob.__table__.c.id_bigint.autoincrement = True
        await conn.run_sync(NodePublishJob.__table__.create)
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
            id=1,
            node_id=node.id,
            workspace_id=ws.id,
            type="quest",
            slug="n1",
            title="N1",
        )
        session.add_all([ws, node, item])
        await session.commit()
        ws_id, node_id, item_id = ws.id, node.id, item.id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, async_session, ws_id, node_id, item_id


@pytest_asyncio.fixture()
async def forbidden_client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(Node.__table__.create)
        await conn.run_sync(NodeItem.__table__.create)
        await conn.run_sync(NodePublishJob.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    app = FastAPI()
    app.include_router(admin_nodes_router.router)

    async def override_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db

    async def forbidden_dep():
        raise HTTPException(status_code=403)

    app.dependency_overrides[admin_nodes_router.admin_required] = forbidden_dep

    async with async_session() as session:
        ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=uuid.uuid4())
        node = Node(
            id=1,
            workspace_id=ws.id,
            slug="n1",
            title="N1",
            content={},
            author_id=uuid.uuid4(),
        )
        item = NodeItem(
            id=1,
            node_id=node.id,
            workspace_id=ws.id,
            type="quest",
            slug="n1",
            title="N1",
        )
        session.add_all([ws, node, item])
        await session.commit()
        ws_id, node_id = ws.id, node.id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, ws_id, node_id


@pytest.mark.asyncio
async def test_publish_info_ok(admin_client):
    client, _, ws_id, node_id, _ = admin_client
    resp = await client.get(f"/admin/workspaces/{ws_id}/nodes/{node_id}/publish_info")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_publish_info_forbidden(forbidden_client):
    client, ws_id, node_id = forbidden_client
    resp = await client.get(f"/admin/workspaces/{ws_id}/nodes/{node_id}/publish_info")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_publish_info_not_found(admin_client):
    client, _, ws_id, node_id, _ = admin_client
    resp = await client.get(f"/admin/workspaces/{ws_id}/nodes/9999/publish_info")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_schedule_publish_ok(admin_client, monkeypatch):
    client, session_factory, ws_id, node_id, _ = admin_client

    orig_init = NodePublishJob.__init__

    def _init(self, **kwargs):
        if "id" not in kwargs:
            kwargs["id"] = 1
        orig_init(self, **kwargs)

    monkeypatch.setattr(NodePublishJob, "__init__", _init)

    payload = {"run_at": datetime.utcnow().isoformat()}
    resp = await client.post(
        f"/admin/workspaces/{ws_id}/nodes/{node_id}/schedule_publish",
        json=payload,
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_schedule_publish_forbidden(forbidden_client):
    client, ws_id, node_id = forbidden_client
    payload = {"run_at": datetime.utcnow().isoformat()}
    resp = await client.post(
        f"/admin/workspaces/{ws_id}/nodes/{node_id}/schedule_publish",
        json=payload,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_schedule_publish_not_found(admin_client):
    client, _, ws_id, node_id, _ = admin_client
    payload = {"run_at": datetime.utcnow().isoformat()}
    resp = await client.post(
        f"/admin/workspaces/{ws_id}/nodes/9999/schedule_publish",
        json=payload,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_cancel_scheduled_publish_ok(admin_client):
    client, session_factory, ws_id, node_id, item_id = admin_client
    async with session_factory() as session:
        job = NodePublishJob(
            id=1,
            workspace_id=ws_id,
            node_id=node_id,
            content_id=item_id,
            access="everyone",
            scheduled_at=datetime.utcnow(),
            status="pending",
        )
        session.add(job)
        await session.commit()

    resp = await client.delete(
        f"/admin/workspaces/{ws_id}/nodes/{node_id}/schedule_publish"
    )
    assert resp.status_code == 200
    assert resp.json()["canceled"] is True


@pytest.mark.asyncio
async def test_cancel_scheduled_publish_forbidden(forbidden_client):
    client, ws_id, node_id = forbidden_client
    resp = await client.delete(
        f"/admin/workspaces/{ws_id}/nodes/{node_id}/schedule_publish"
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_cancel_scheduled_publish_not_found(admin_client):
    client, _, ws_id, node_id, _ = admin_client
    resp = await client.delete(
        f"/admin/workspaces/{ws_id}/nodes/{node_id}/schedule_publish"
    )
    assert resp.status_code == 404
