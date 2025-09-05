import importlib
import sys
import types
import uuid

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Ensure app package resolves
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

# Stub security module
security_stub = types.ModuleType("app.security")
security_stub.ADMIN_AUTH_RESPONSES = {}


def require_admin_role():
    async def _dep():
        return types.SimpleNamespace(id=uuid.uuid4())

    return _dep


security_stub.require_admin_role = require_admin_role
sys.modules["app.security"] = security_stub

from app.domains.nodes.api.admin_nodes_global_router import (  # noqa: E402
    router as admin_router,
)
from app.domains.nodes.infrastructure.models.node import Node  # noqa: E402
from app.domains.quests.infrastructure.models import quest_models  # noqa: F401, E402
from app.domains.tags.infrastructure.models.tag_models import NodeTag  # noqa: E402
from app.domains.tags.models import Tag  # noqa: E402
from app.domains.workspaces.infrastructure.models import Workspace  # noqa: E402
from app.providers.db.session import get_db  # noqa: E402


@pytest_asyncio.fixture()
async def app_and_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        # Allow null workspace_id for tests
        Node.__table__.c.workspace_id.nullable = True
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(Tag.__table__.create)
        await conn.run_sync(Node.__table__.create)
        await conn.run_sync(NodeTag.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    app = FastAPI()
    app.include_router(admin_router)

    async def override_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    return app, async_session


@pytest.mark.asyncio
async def test_get_global_node(app_and_session):
    app, async_session = app_and_session
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
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/admin/nodes/{node_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == node_id


@pytest.mark.asyncio
async def test_get_global_node_includes_tags(app_and_session):
    app, async_session = app_and_session
    async with async_session() as session:
        tag = Tag(id=uuid.uuid4(), slug="t1", name="T1", workspace_id=uuid.uuid4())
        node = Node(
            id=4,
            slug="n4",
            title="N4",
            content={},
            media=[],
            author_id=uuid.uuid4(),
            tags=[tag],
        )
        session.add_all([tag, node])
        await session.commit()
        node_id = node.id
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/admin/nodes/{node_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tags"] == ["t1"]


@pytest.mark.asyncio
async def test_put_global_node_updates(app_and_session):
    app, async_session = app_and_session
    async with async_session() as session:
        node = Node(
            id=3,
            slug="n3",
            title="N3",
            content={},
            media=[],
            author_id=uuid.uuid4(),
        )
        session.add(node)
        await session.commit()
        node_id = node.id
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(f"/admin/nodes/{node_id}", json={"title": "NX"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == node_id
    assert data["title"] == "NX"
    async with async_session() as session:
        updated = await session.get(Node, node_id)
        assert updated.title == "NX"


@pytest.mark.asyncio
async def test_get_global_node_not_found(app_and_session):
    app, async_session = app_and_session
    async with async_session() as session:
        ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=uuid.uuid4())
        session.add(ws)
        node = Node(
            id=2,
            workspace_id=ws.id,
            slug="n2",
            title="N2",
            content={},
            media=[],
            author_id=uuid.uuid4(),
        )
        session.add_all([ws, node])
        await session.commit()
        node_id = node.id
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/admin/nodes/{node_id}")
    assert resp.status_code == 404
