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
domains_module = importlib.import_module("apps.backend.app.domains")
sys.modules.setdefault("app.domains", domains_module)
security_stub = types.ModuleType("app.security")
security_stub.ADMIN_AUTH_RESPONSES = {}
security_stub.bearer_scheme = lambda: None
security_stub.require_ws_guest = lambda workspace_id=None: None
security_stub.require_ws_viewer = lambda workspace_id=None, user=None, db=None: None
security_stub.auth_user = lambda: None
sys.modules["app.security"] = security_stub

from app.api import deps as api_deps  # noqa: E402
from app.domains.quests.api.versions_router import (  # noqa: E402
    router as versions_router,  # noqa: E402
)
from app.domains.quests.infrastructure.models.quest_models import Quest  # noqa: E402
from app.domains.quests.infrastructure.models.quest_version_models import (  # noqa: E402
    QuestGraphEdge,
    QuestGraphNode,
    QuestVersion,
)
from app.domains.users.infrastructure.models.user import User  # noqa: E402
from app.domains.workspaces.infrastructure.models import Workspace  # noqa: E402
from app.providers.db.session import get_db  # noqa: E402


@pytest_asyncio.fixture()
async def app_and_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(Quest.__table__.create)
        await conn.run_sync(QuestVersion.__table__.create)
        await conn.run_sync(QuestGraphNode.__table__.create)
        await conn.run_sync(QuestGraphEdge.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    app = FastAPI()
    app.include_router(versions_router)

    async def override_db():
        async with async_session() as session:
            yield session

    user = User(id=uuid.uuid4(), is_active=True, role="user", is_premium=False)
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[api_deps.get_current_user] = lambda: user

    return app, async_session, user


@pytest.mark.asyncio
async def test_get_current_version_returns_graph(app_and_session):
    app, async_session, user = app_and_session
    async with async_session() as session:
        ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user.id)
        session.add(ws)
        quest_id = uuid.uuid4()
        quest = Quest(
            id=quest_id, workspace_id=ws.id, slug="q", title="Quest", author_id=user.id
        )
        session.add(quest)
        version = QuestVersion(
            id=uuid.uuid4(), quest_id=quest_id, number=1, status="released"
        )
        session.add(version)
        node_start = QuestGraphNode(version_id=version.id, key="start", title="Start")
        node_end = QuestGraphNode(version_id=version.id, key="end", title="End")
        edge = QuestGraphEdge(
            version_id=version.id, from_node_key="start", to_node_key="end"
        )
        session.add_all([node_start, node_end, edge])
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            f"/quests/{quest_id}/versions/current", params={"workspace_id": str(ws.id)}
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"]["id"] == str(version.id)
    assert data["steps"][0]["key"] == "start"
