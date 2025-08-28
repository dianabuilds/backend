import importlib
import sys
import types
import uuid
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Ensure app package resolves
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.core.db.session import get_db  # noqa: E402
from app.domains.nodes.application.node_service import NodeService  # noqa: E402
from app.domains.nodes.models import NodeItem, NodePatch  # noqa: E402
from app.domains.users.infrastructure.models.user import User  # noqa: E402
from app.schemas.nodes_common import NodeType, Status  # noqa: E402

# Stub security before importing router
security_stub = types.ModuleType("app.security")
security_stub.ADMIN_AUTH_RESPONSES = {}
security_stub.bearer_scheme = None
security_stub.auth_user = lambda: User(id=uuid.uuid4(), is_premium=False, role="user")
security_stub.require_ws_editor = lambda workspace_id=None: None
sys.modules.setdefault("app.security", security_stub)

from app.domains.nodes.content_admin_router import router as nodes_router  # noqa: E402


@pytest.mark.asyncio
async def test_node_service_rejects_quest_data():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(NodeItem.__table__.create)
        await conn.run_sync(NodePatch.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        node = NodeItem(
            id=uuid.uuid4(),
            workspace_id=uuid.uuid4(),
            type=NodeType.article.value,
            slug="slug-1",
            title="Title",
            status=Status.draft,
            created_by_user_id=uuid.uuid4(),
        )
        session.add(node)
        await session.commit()
        svc = NodeService(session)
        with pytest.raises(HTTPException) as exc:
            await svc.update(
                node.workspace_id,
                NodeType.article,
                node.id,
                {"quest_data": {}},
                actor_id=node.created_by_user_id,
            )
        assert exc.value.status_code == 422
        assert "/quests" in exc.value.detail


@pytest_asyncio.fixture()
async def app_and_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    app = FastAPI()
    app.include_router(nodes_router)

    async def override_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db

    return app, async_session


@pytest.mark.asyncio
async def test_router_rejects_quest_data(app_and_session):
    app, async_session = app_and_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.patch(
            f"/admin/nodes/article/{uuid.uuid4()}",
            params={"workspace_id": str(uuid.uuid4())},
            json={"quest_data": {}},
        )
    assert resp.status_code == 422
    assert "/quests" in resp.json()["detail"]
