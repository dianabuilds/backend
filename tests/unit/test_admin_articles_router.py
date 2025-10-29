import importlib
import sys
import types
import uuid
from pathlib import Path

import pytest
import pytest_asyncio
import sqlalchemy as sa
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Ensure "app" package resolves correctly
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

# Stub security dependencies used by the router
security_stub = types.ModuleType("app.security")
security_stub.ADMIN_AUTH_RESPONSES = {}


async def auth_user():
    return types.SimpleNamespace(id=uuid.uuid4())


def require_ws_editor():
    async def _dep(
        workspace_id: uuid.UUID,
        user: object | None = None,
        db: object | None = None,
    ) -> types.SimpleNamespace:
        return types.SimpleNamespace(role="editor")

    return _dep


security_stub.auth_user = auth_user
security_stub.require_ws_editor = require_ws_editor
sys.modules.setdefault("app.security", security_stub)

from app.core.db.session import get_db  # noqa: E402
from app.domains.nodes.api.articles_admin_router import (  # noqa: E402
    router as articles_router,
)
from app.domains.nodes.application.node_service import NodeService  # noqa: E402
from app.domains.nodes.models import NodeItem, NodePatch  # noqa: E402
from app.domains.tags.models import Tag  # noqa: E402
from app.domains.workspaces.infrastructure.models import Workspace  # noqa: E402
from app.schemas.nodes_common import NodeType  # noqa: E402

users_table = NodeItem.__table__.metadata.tables["users"]


@pytest_asyncio.fixture()
async def app_and_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(users_table.create)
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(Tag.__table__.create)
        await conn.run_sync(NodeItem.__table__.create)
        await conn.run_sync(NodePatch.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    app = FastAPI()
    app.include_router(articles_router)

    async def override_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    return app, async_session


@pytest.mark.asyncio
async def test_get_article(app_and_session):
    app, async_session = app_and_session
    async with async_session() as session:
        user_id = uuid.uuid4()
        await session.execute(sa.insert(users_table).values(id=str(user_id)))
        ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user_id)
        session.add(ws)
        await session.commit()
        svc = NodeService(session)
        item = await svc.create(ws.id, NodeType.article, actor_id=user_id)
        article_id = item.id
        ws_id = ws.id
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/admin/workspaces/{ws_id}/articles/{article_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(article_id)
    assert data["workspace_id"] == str(ws_id)
