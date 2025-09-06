import importlib
import sys
import types
import uuid

import pytest
import pytest_asyncio
import sqlalchemy as sa
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.api import deps as api_deps  # noqa: E402
from app.api.workspace_context import optional_workspace  # noqa: E402
from app.domains.nodes.api.nodes_router import router as nodes_router  # noqa: E402
from app.domains.nodes.infrastructure.models.node import Node  # noqa: E402
from app.domains.nodes.models import NodeItem  # noqa: E402
from app.providers.db.session import get_db  # noqa: E402
from app.schemas.nodes_common import Status, Visibility  # noqa: E402
from app.schemas.workspaces import WorkspaceRole  # noqa: E402
from app.security import require_ws_guest  # noqa: E402


@pytest_asyncio.fixture()
async def app_and_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    metadata = NodeItem.__table__.metadata
    workspace_tbl = metadata.tables.get("workspaces")
    if workspace_tbl is None:
        workspace_tbl = sa.Table(
            "workspaces",
            metadata,
            sa.Column("id", sa.Integer, primary_key=True),
        )
    elif "id" not in workspace_tbl.c:
        workspace_tbl.append_column(sa.Column("id", sa.Integer, primary_key=True))
    async with engine.begin() as conn:
        await conn.run_sync(workspace_tbl.create)
        Node.__table__.c.id.type = sa.Integer()
        Node.__table__.c.account_id.type = sa.Integer()
        await conn.run_sync(Node.__table__.create)
        NodeItem.__table__.c.id_bigint.type = sa.Integer()
        NodeItem.__table__.c.workspace_id.type = sa.Integer()
        await conn.run_sync(NodeItem.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    app = FastAPI()
    app.include_router(nodes_router)
    app.include_router(nodes_router, prefix="/workspaces/{workspace_id}")

    async def override_db():
        async with async_session() as session:
            yield session

    user = types.SimpleNamespace(id=uuid.uuid4(), role="user")
    member = types.SimpleNamespace(role=WorkspaceRole.viewer)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[api_deps.get_current_user] = lambda: user
    app.dependency_overrides[optional_workspace] = lambda: None
    app.dependency_overrides[require_ws_guest] = lambda **_: member

    return app, async_session, user


@pytest.mark.asyncio
async def test_scope_modes(app_and_session):
    app, async_session, user = app_and_session
    async with async_session() as session:
        ws_id = 1
        await session.execute(sa.text("INSERT INTO workspaces (id) VALUES (:id)"), {"id": ws_id})
        node = Node(
            account_id=ws_id,
            slug="n1",
            title="N1",
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
            id=1,
            node_id=node.id,
            workspace_id=ws_id,
            type="node",
            slug=node.slug,
            title=node.title,
            status=Status.published,
            visibility=Visibility.public,
        )
        session.add(item)
        await session.commit()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        for mode in ["mine", "member", "invited"]:
            resp = await ac.get(f"/workspaces/{ws_id}/nodes", params={"scope_mode": mode})
            assert resp.status_code == 200
        resp = await ac.get("/nodes", params={"scope_mode": f"space:{ws_id}"})
        assert resp.status_code == 200
        resp = await ac.get("/nodes", params={"scope_mode": "global"})
        assert resp.status_code == 403
