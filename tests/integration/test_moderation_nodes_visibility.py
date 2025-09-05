import types
import uuid

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.domains.moderation.api.nodes_router import admin_required
from app.domains.moderation.api.nodes_router import router as mod_nodes_router
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.tags.infrastructure.models.tag_models import NodeTag
from app.domains.tags.models import Tag
from app.domains.workspaces.infrastructure.models import Workspace
from app.providers.db.session import get_db


@pytest_asyncio.fixture()
async def client_with_node():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(Node.__table__.create)
        await conn.run_sync(Tag.__table__.create)
        await conn.run_sync(NodeTag.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    app = FastAPI()
    app.include_router(mod_nodes_router)

    async def override_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db

    user = types.SimpleNamespace(id=uuid.uuid4())
    app.dependency_overrides[admin_required] = lambda: user

    async with async_session() as session:
        ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user.id)
        node = Node(
            id=1,
            workspace_id=ws.id,
            slug="n1",
            title="N1",
            author_id=user.id,
            is_visible=False,
        )
        session.add_all([ws, node])
        await session.commit()
        ws_id, slug = ws.id, node.slug

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, async_session, ws_id, slug


@pytest.mark.asyncio
async def test_restore_and_hide(client_with_node):
    client, async_session, ws_id, slug = client_with_node

    resp = await client.post(f"/admin/workspaces/{ws_id}/moderation/nodes/{slug}/restore")
    assert resp.status_code == 200
    async with async_session() as session:
        node = await session.get(Node, 1)
        assert node.is_visible is True

    resp = await client.post(
        f"/admin/workspaces/{ws_id}/moderation/nodes/{slug}/hide",
        json={"reason": ""},
    )
    assert resp.status_code == 200
    async with async_session() as session:
        node = await session.get(Node, 1)
        assert node.is_visible is False
