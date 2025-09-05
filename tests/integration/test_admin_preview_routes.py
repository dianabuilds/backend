from __future__ import annotations

import types
import uuid
from dataclasses import dataclass

import pytest
import pytest_asyncio
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.preview import PreviewContext
from app.domains.navigation.api import preview_router as preview_module
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.tags.infrastructure.models.tag_models import NodeTag
from app.domains.tags.models import Tag
from app.domains.users.infrastructure.models.user import User
from app.domains.workspaces.infrastructure.models import Workspace
from app.providers.db.session import get_db


@pytest_asyncio.fixture()
async def preview_setup(monkeypatch):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(Node.__table__.create)
        await conn.run_sync(Tag.__table__.create)
        await conn.run_sync(NodeTag.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    app = FastAPI()
    app.include_router(preview_module.router)

    async def override_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db

    @dataclass
    class DummyTrace:
        selected: bool
        policy: str | None = None

    class DummyNavigationService:
        def __init__(self) -> None:
            self._router = types.SimpleNamespace(history=[])

        async def build_route(
            self, db, node, user, preview: PreviewContext | None = None, mode=None
        ):
            trace = [DummyTrace(selected=True, policy="p")]
            return types.SimpleNamespace(
                next=types.SimpleNamespace(slug="n2", tags=[]),
                reason=None,
                trace=trace,
                metrics={},
            )

        async def get_next(self, db, node, user, preview: PreviewContext | None = None, mode=None):
            return await self.build_route(db, node, user, preview=preview, mode=mode)

    monkeypatch.setattr(preview_module, "NavigationService", DummyNavigationService)
    monkeypatch.setattr(preview_module, "create_preview_token", lambda *a, **k: "fake-token")

    admin_dep = None
    simulate_dep = None
    for route in preview_module.router.routes:
        if route.path == "/admin/preview/link" and "POST" in route.methods:
            admin_dep = route.dependant.dependencies[0].call
        elif route.path == "/admin/preview/transitions/simulate" and "POST" in route.methods:
            simulate_dep = route.dependant.dependencies[0].call
    assert admin_dep and simulate_dep

    async with async_session() as session:
        ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=uuid.uuid4())
        user = User(id=uuid.uuid4())
        node = Node(id=1, workspace_id=ws.id, slug="start", author_id=user.id)
        session.add_all([ws, user, node])
        await session.commit()
        ws_id = ws.id

    return app, ws_id, admin_dep, simulate_dep


@pytest.mark.asyncio
async def test_create_preview_link_ok(preview_setup):
    app, ws_id, admin_dep, _ = preview_setup
    app.dependency_overrides[admin_dep] = lambda: None
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/admin/preview/link", json={"workspace_id": str(ws_id)})
    assert resp.status_code == 200
    assert resp.json()["url"].endswith("fake-token")


@pytest.mark.asyncio
async def test_create_preview_link_forbidden(preview_setup):
    app, ws_id, admin_dep, _ = preview_setup

    async def forbidden():
        raise HTTPException(status_code=403)

    app.dependency_overrides[admin_dep] = forbidden
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/admin/preview/link", json={"workspace_id": str(ws_id)})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_simulate_transitions_ok(preview_setup):
    app, ws_id, _, simulate_dep = preview_setup
    app.dependency_overrides[simulate_dep] = lambda: None
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/admin/preview/transitions/simulate",
            json={"workspace_id": str(ws_id), "start": "start"},
        )
    assert resp.status_code == 200
    assert "next" in resp.json()


@pytest.mark.asyncio
async def test_simulate_transitions_forbidden(preview_setup):
    app, ws_id, _, simulate_dep = preview_setup

    async def forbidden():
        raise HTTPException(status_code=403)

    app.dependency_overrides[simulate_dep] = forbidden
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/admin/preview/transitions/simulate",
            json={"workspace_id": str(ws_id), "start": "start"},
        )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_simulate_transitions_not_found(preview_setup):
    app, ws_id, _, simulate_dep = preview_setup
    app.dependency_overrides[simulate_dep] = lambda: None
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/admin/preview/transitions/simulate",
            json={"workspace_id": str(uuid.uuid4()), "start": "start"},
        )
    assert resp.status_code == 404
