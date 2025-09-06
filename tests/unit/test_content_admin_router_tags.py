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

module_name = "app.domains.nodes.application.editorjs_renderer"
sys.modules.setdefault(
    module_name,
    types.SimpleNamespace(
        collect_unknown_blocks=lambda *_a, **_k: [],
        render_html=lambda *_a, **_k: "",
    ),
)

from app.domains.nodes.content_admin_router import router as admin_router  # noqa: E402
from app.domains.nodes.infrastructure.models.node import Node  # noqa: E402
from app.domains.nodes.models import NodeItem, NodePatch  # noqa: E402
from app.domains.tags.infrastructure.models.tag_models import NodeTag  # noqa: E402
from app.domains.tags.models import ContentTag, Tag  # noqa: E402
from app.domains.workspaces.infrastructure.models import Workspace  # noqa: E402
from app.providers.db.session import get_db  # noqa: E402
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
        await conn.run_sync(ContentTag.__table__.create)
        await conn.run_sync(NodePatch.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    app = FastAPI()
    app.include_router(admin_router)

    import app.domains.nodes.application.node_service as ns

    async def _noop(*_a, **_k) -> None:
        return None

    ns.navsvc = types.SimpleNamespace(invalidate_navigation_cache=_noop)
    ns.navcache = types.SimpleNamespace(
        invalidate_navigation_by_node=_noop,
        invalidate_modes_by_node=_noop,
        invalidate_compass_all=_noop,
    )

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
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, ws.id, async_session


@pytest.mark.asyncio
async def test_patch_returns_tags(app_client):
    client, acc_id, async_session = app_client
    async with async_session() as session:
        node = Node(
            id=1,
            workspace_id=acc_id,
            slug="article-1",
            title="New article",
            content={},
            author_id=uuid.uuid4(),
        )
        item = NodeItem(
            id=2,
            node_id=node.id,
            workspace_id=acc_id,
            type="article",
            slug="article-1",
            title="New article",
        )
        session.add_all([node, item])
        await session.commit()
        node_id = item.id

    resp = await client.patch(
        f"/admin/accounts/{acc_id}/nodes/types/article/{node_id}",
        json={"tags": ["t1", "t2"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert sorted(data["tags"]) == ["t1", "t2"]
