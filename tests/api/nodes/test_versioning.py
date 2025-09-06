from __future__ import annotations

# ruff: noqa: E402
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

# Ensure app package resolves
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

module_name = "app.domains.nodes.application.editorjs_renderer"
_editorjs = types.ModuleType("editorjs_renderer")
_editorjs.collect_unknown_blocks = lambda *args, **kwargs: []  # type: ignore[assign]
_editorjs.render_html = lambda *args, **kwargs: ""  # type: ignore[assign]
sys.modules.setdefault(module_name, _editorjs)

from app.api import deps as api_deps  # noqa: E402
from app.domains.admin.infrastructure.models.audit_log import AuditLog  # noqa: E402
from app.domains.nodes.api.admin_nodes_router import (  # noqa: E402
    admin_required,
)
from app.domains.nodes.api.admin_nodes_router import (
    router as admin_router,
)
from app.domains.nodes.api.nodes_router import router as nodes_router  # noqa: E402
from app.domains.nodes.infrastructure.models.node import Node  # noqa: E402
from app.domains.nodes.infrastructure.models.node_version import NodeVersion  # noqa: E402
from app.domains.nodes.infrastructure.repositories.node_repository import (
    NodeRepository,
)  # noqa: E402
from app.domains.nodes.models import NodeItem  # noqa: E402
from app.domains.tags.infrastructure.models.tag_models import NodeTag  # noqa: E402
from app.domains.tags.models import Tag  # noqa: E402
from app.domains.workspaces.infrastructure.models import Workspace  # noqa: E402
from app.providers.db.session import get_db  # noqa: E402
from app.schemas.node import NodeUpdate  # noqa: E402
from app.schemas.nodes_common import Status, Visibility  # noqa: E402
from app.security import require_ws_guest  # noqa: E402

workspace_stub = sa.Table(
    "workspaces",
    NodeItem.__table__.metadata,
    sa.Column("id", sa.Integer, primary_key=True),
)


@pytest_asyncio.fixture()
async def app_and_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        Workspace.__table__.c.id.type = sa.Integer()
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(workspace_stub.create)
        Tag.__table__.c.id.type = sa.Integer()
        Tag.__table__.c.workspace_id.type = sa.Integer()
        await conn.run_sync(Tag.__table__.create)
        Node.__table__.c.id.type = sa.Integer()
        Node.__table__.c.account_id.type = sa.Integer()
        Node.__table__.c.meta.type = sa.JSON()
        await conn.run_sync(Node.__table__.create)
        NodeTag.__table__.c.node_id.type = sa.Integer()
        NodeTag.__table__.c.tag_id.type = sa.Integer()
        await conn.run_sync(NodeTag.__table__.create)
        NodeVersion.__table__.c.node_id.type = sa.Integer()
        NodeVersion.__table__.c.meta.type = sa.JSON()
        NodeVersion.__table__.c.created_by_user_id.type = sa.String()
        await conn.run_sync(NodeVersion.__table__.create)
        NodeItem.__table__.c.id_bigint.type = sa.Integer()
        NodeItem.__table__.c.workspace_id.type = sa.Integer()
        await conn.run_sync(NodeItem.__table__.create)
        AuditLog.__table__.c.workspace_id.type = sa.Integer()
        AuditLog.__table__.c.actor_id.type = sa.String()
        await conn.run_sync(AuditLog.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    app = FastAPI()
    app.include_router(nodes_router)
    app.include_router(nodes_router, prefix="/accounts/{account_id}")
    app.include_router(admin_router)

    async def override_db():
        async with async_session() as session:
            yield session

    user = types.SimpleNamespace(id=uuid.uuid4(), role="admin")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[api_deps.get_current_user] = lambda: user
    app.dependency_overrides[api_deps.get_current_user_optional] = lambda: user

    nodes_router.require_ws_guest = lambda account_id, user, db: None
    app.dependency_overrides[require_ws_guest] = lambda **_: None
    app.dependency_overrides[admin_required] = lambda: user

    return app, async_session, user


@pytest.mark.asyncio
async def test_preview_version(app_and_session):
    app, async_session, user = app_and_session
    ws_id = 1
    async with async_session() as session:
        ws = Workspace(id=ws_id, name="W", slug="w", owner_user_id=user.id)
        node = Node(
            account_id=ws_id,
            slug="n1",
            title="V1",
            meta={},
            author_id=user.id,
            is_visible=True,
            allow_feedback=True,
            is_recommendable=True,
        )
        session.add_all([ws, node])
        await session.commit()
        repo = NodeRepository(session)
        await repo.update(node, NodeUpdate(title="V2"), user.id)
        slug = node.slug
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            f"/accounts/{ws_id}/nodes/{slug}",
            headers={"X-Preview-Version": "1"},
        )
    assert resp.status_code == 200
    assert resp.json()["title"] == "V1"


@pytest.mark.asyncio
async def test_rollback_creates_audit_entry(app_and_session):
    app, async_session, user = app_and_session
    ws_uuid = uuid.UUID(int=1)
    ws_id = ws_uuid.int
    async with async_session() as session:
        ws = Workspace(id=ws_id, name="W", slug="w", owner_user_id=user.id)
        node = Node(
            id=1,
            account_id=ws_id,
            slug="n1",
            title="V1",
            meta={},
            author_id=user.id,
            is_visible=True,
            allow_feedback=True,
            is_recommendable=True,
        )
        session.add_all([ws, node])
        await session.commit()
        repo = NodeRepository(session)
        await repo.update(node, NodeUpdate(title="V2"), user.id)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(f"/admin/accounts/{ws_uuid}/nodes/1/versions/1/rollback")
    assert resp.status_code == 200
    async with async_session() as session:
        refreshed = await session.get(Node, 1)
        assert refreshed.title == "V1"
        logs = (await session.execute(sa.select(AuditLog))).scalars().all()
        assert logs and logs[0].action == "node_version_rollback"


@pytest.mark.asyncio
async def test_publish_node(app_and_session):
    app, async_session, user = app_and_session
    ws_uuid = uuid.UUID(int=1)
    ws_id = ws_uuid.int
    async with async_session() as session:
        ws = Workspace(id=ws_id, name="W", slug="w", owner_user_id=user.id)
        node = Node(
            id=1,
            account_id=ws_id,
            slug="n1",
            title="N1",
            meta={},
            author_id=user.id,
            is_visible=True,
            allow_feedback=True,
            is_recommendable=True,
        )
        item = NodeItem(
            id=1,
            node_id=node.id,
            workspace_id=ws_id,
            type="node",
            slug=node.slug,
            title=node.title,
            status=Status.draft,
            visibility=Visibility.private,
            created_by_user_id=user.id,
        )
        session.add_all([ws, node, item])
        await session.commit()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(f"/admin/accounts/{ws_uuid}/nodes/{node.id}/publish")
    assert resp.status_code == 200
    assert resp.json()["status"] == "published"
    async with async_session() as session:
        db_item = await session.get(NodeItem, item.id)
        assert db_item.status == Status.published
        db_node = await session.get(Node, node.id)
        assert db_node.status == Status.published
