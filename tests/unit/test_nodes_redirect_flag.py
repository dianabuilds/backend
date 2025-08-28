import sys
import types
import uuid
import importlib
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
domains_module = importlib.import_module("apps.backend.app.domains")
sys.modules.setdefault("app.domains", domains_module)
security_stub = types.ModuleType("app.security")
security_stub.ADMIN_AUTH_RESPONSES = {}
security_stub.bearer_scheme = lambda: None
security_stub.require_ws_guest = lambda workspace_id=None: None
security_stub.require_ws_viewer = lambda workspace_id=None, user=None, db=None: None
security_stub.auth_user = lambda: None
sys.modules["app.security"] = security_stub

from app.core import policy as core_policy  # noqa: E402
core_policy.policy.allow_write = False
import app.domains.navigation.application.traces_service as traces_service  # noqa: E402
from app.api import deps as api_deps  # noqa: E402
from app.core.db.session import get_db  # noqa: E402
from app.core.workspace_context import optional_workspace  # noqa: E402
from app.domains.nodes.api.nodes_router import router as nodes_router  # noqa: E402
from app.domains.nodes.infrastructure.models.node import Node  # noqa: E402
from app.domains.nodes.models import NodeItem  # noqa: E402
from app.domains.tags.infrastructure.models.tag_models import NodeTag  # noqa: E402
from app.domains.tags.models import Tag  # noqa: E402
from app.domains.admin.infrastructure.models.feature_flag import FeatureFlag  # noqa: E402
from app.domains.users.infrastructure.models.user import User  # noqa: E402
from app.domains.workspaces.infrastructure.models import Workspace  # noqa: E402
from app.schemas.nodes_common import Status, Visibility  # noqa: E402


@pytest_asyncio.fixture()
async def app_and_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(Node.__table__.create)
        await conn.run_sync(NodeItem.__table__.create)
        await conn.run_sync(Tag.__table__.create)
        await conn.run_sync(NodeTag.__table__.create)
        await conn.run_sync(FeatureFlag.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    app = FastAPI()
    app.include_router(nodes_router)

    async def override_db():
        async with async_session() as session:
            yield session

    user = User(id=uuid.uuid4(), is_active=True, role="user", is_premium=False)
    security_stub.auth_user = lambda: user
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[api_deps.get_current_user] = lambda: user
    app.dependency_overrides[optional_workspace] = lambda: None

    async def _noop(self, db, node, user, chance=0.3):
        return None
    traces_service.TracesService.maybe_add_auto_trace = _noop  # type: ignore[assignment]

    return app, async_session, user


@pytest.mark.asyncio
async def test_nodes_redirect_flag(app_and_session):
    app, async_session, user = app_and_session
    async with async_session() as session:
        ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user.id)
        session.add(ws)
        node_id = uuid.uuid4()
        slug = "quest-node"
        node = Node(
            id=node_id,
            workspace_id=ws.id,
            slug=slug,
            title="Quest",
            content={},
            media=[],
            author_id=user.id,
            is_visible=True,
            is_public=True,
            premium_only=False,
            is_recommendable=True,
        )
        session.add(node)
        item = NodeItem(
            id=uuid.uuid4(),
            node_id=node_id,
            workspace_id=ws.id,
            type="quest",
            slug=slug,
            title="Quest",
            status=Status.published,
            visibility=Visibility.public,
            created_by_user_id=user.id,
            quest_data={"steps": [1]},
        )
        session.add(item)
        session.add(FeatureFlag(key="quests.nodes_redirect", value=True))
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/nodes/{slug}", params={"workspace_id": str(ws.id)})
    assert resp.status_code == 307
    assert resp.headers["location"] == f"/quests/{node_id}/versions/current?workspace_id={ws.id}"
