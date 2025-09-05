from __future__ import annotations

import types
import uuid

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.domains.moderation.api.cases_router import admin_required, router
from app.domains.moderation.infrastructure.models.moderation_case_models import (
    CaseAttachment,
    CaseEvent,
    CaseLabel,
    CaseNote,
    ModerationCase,
    ModerationLabel,
)
from app.security.exceptions import AuthError


@pytest_asyncio.fixture()
async def app_and_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(ModerationCase.__table__.create)
        await conn.run_sync(CaseAttachment.__table__.create)
        await conn.run_sync(CaseNote.__table__.create)
        await conn.run_sync(CaseEvent.__table__.create)
        await conn.run_sync(ModerationLabel.__table__.create)
        await conn.run_sync(CaseLabel.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    app = FastAPI()
    app.include_router(router)

    @app.exception_handler(AuthError)
    async def handle_auth_error(_, exc: AuthError):  # pragma: no cover - simple adapter
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.code})

    async def override_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    return app, async_session


@pytest.mark.asyncio
async def test_requires_admin(app_and_session):
    app, _ = app_and_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/admin/moderation/cases")
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_case_creation_and_listing(app_and_session):
    app, _ = app_and_session
    admin = types.SimpleNamespace(id=uuid.uuid4())
    app.dependency_overrides[admin_required] = lambda: admin

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"type": "support_request", "summary": "hello"}
        resp = await client.post("/admin/moderation/cases", json=payload)
        assert resp.status_code == 200

        resp = await client.get("/admin/moderation/cases")
        data = resp.json()
        assert data["total"] == 1


@pytest.mark.asyncio
async def test_patch_labels_endpoint(app_and_session):
    app, _ = app_and_session
    admin = types.SimpleNamespace(id=uuid.uuid4())
    app.dependency_overrides[admin_required] = lambda: admin

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"type": "support_request", "summary": "hi"}
        resp = await client.post("/admin/moderation/cases", json=payload)
        case_id = resp.json()["id"]

        resp = await client.patch(
            f"/admin/moderation/cases/{case_id}/labels", json={"add": ["spam"]}
        )
        assert resp.status_code == 200
        assert resp.json()["labels"] == ["spam"]

        resp = await client.patch(
            f"/admin/moderation/cases/{case_id}/labels",
            json={"add": ["bug"], "remove": ["spam"]},
        )
        assert resp.status_code == 200
        assert resp.json()["labels"] == ["bug"]

@pytest.mark.asyncio
async def test_close_case(app_and_session):
    app, session_factory = app_and_session
    admin = types.SimpleNamespace(id=uuid.uuid4())
    app.dependency_overrides[admin_required] = lambda: admin

    async with session_factory() as session:
        case = ModerationCase(type="support_request", summary="close me")
        session.add(case)
        await session.commit()
        case_id = case.id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/admin/moderation/cases/{case_id}/actions/close",
            json={"resolution": "resolved"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    async with session_factory() as session:
        refreshed = await session.get(ModerationCase, case_id)
        assert refreshed.status == "resolved"
        assert refreshed.resolution == "resolved"

