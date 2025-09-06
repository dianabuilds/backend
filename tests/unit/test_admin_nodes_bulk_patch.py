# ruff: noqa: E402
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

# Ensure "app" package resolves correctly
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
sys.modules.setdefault("app.security", security_stub)

from app.domains.navigation.infrastructure.models.transition_models import (  # noqa: E402
    NodeTransition,
)
from app.domains.nodes.api.admin_nodes_router import (
    router as admin_router,  # noqa: E402
)
from app.domains.nodes.infrastructure.models.node import Node  # noqa: E402
from app.domains.tags.infrastructure.models.tag_models import NodeTag  # noqa: E402
from app.domains.tags.models import Tag  # noqa: E402
from app.domains.workspaces.infrastructure.models import Workspace  # noqa: E402
from app.providers.db.session import get_db  # noqa: E402


# Patch navcache to no-op implementation
class DummyNav:
    async def invalidate_navigation_by_node(
        self, account_id: object, slug: str
    ) -> None:  # noqa: ANN401
        return None

    async def invalidate_modes_by_node(self, account_id: object, slug: str) -> None:  # noqa: ANN401
        return None

    async def invalidate_compass_all(self) -> None:
        return None


admin_router.navcache = DummyNav()


@pytest_asyncio.fixture()
async def app_and_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(Tag.__table__.create)
        await conn.run_sync(Node.__table__.create)
        await conn.run_sync(NodeTag.__table__.create)
        await conn.run_sync(NodeTransition.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    app = FastAPI()
    app.include_router(admin_router)

    async def override_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    return app, async_session


@pytest.mark.asyncio
async def test_bulk_patch_updates_flags(app_and_session):
    app, async_session = app_and_session
    async with async_session() as session:
        ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=uuid.uuid4())
        session.add(ws)
        await session.commit()
        n1 = Node(
            account_id=ws.id,
            slug="n1",
            title="N1",
            content={},
            media=[],
            author_id=uuid.uuid4(),
            is_visible=True,
            is_public=False,
            premium_only=False,
            is_recommendable=True,
        )
        n2 = Node(
            account_id=ws.id,
            slug="n2",
            title="N2",
            content={},
            media=[],
            author_id=uuid.uuid4(),
            is_visible=True,
            is_public=False,
            premium_only=False,
            is_recommendable=True,
        )
        session.add_all([n1, n2])
        await session.commit()
        ids = [n1.id, n2.id]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.patch(
            f"/admin/accounts/{ws.id}/nodes/bulk",
            json={
                "ids": ids,
                "changes": {
                    "is_visible": False,
                    "is_public": True,
                    "premium_only": True,
                    "is_recommendable": False,
                },
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert set(map(int, data["updated"])) == set(ids)
    async with async_session() as session:
        node1 = await session.get(Node, ids[0])
        node2 = await session.get(Node, ids[1])
        assert node1.is_visible is False
        assert node1.is_public is True
        assert node1.premium_only is True
        assert node1.is_recommendable is False
        assert node2.is_visible is False
        assert node2.is_public is True
        assert node2.premium_only is True
        assert node2.is_recommendable is False


@pytest.mark.asyncio
async def test_bulk_patch_delete(app_and_session):
    app, async_session = app_and_session
    async with async_session() as session:
        ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=uuid.uuid4())
        session.add(ws)
        await session.commit()
        n1 = Node(
            account_id=ws.id,
            slug="n1",
            title="N1",
            content={},
            media=[],
            author_id=uuid.uuid4(),
        )
        session.add(n1)
        await session.commit()
        node_id = n1.id
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.patch(
            f"/admin/accounts/{ws.id}/nodes/bulk",
            json={"ids": [node_id], "changes": {"delete": True}},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert list(map(int, data["deleted"])) == [node_id]
    async with async_session() as session:
        node = await session.get(Node, node_id)
        assert node is None
