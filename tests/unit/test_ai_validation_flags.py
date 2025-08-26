import importlib
import sys
import types
import uuid
from pathlib import Path

# ruff: noqa: E402
import pytest
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Ensure app package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

# Stub security module
security_stub = types.ModuleType("app.security")
security_stub.ADMIN_AUTH_RESPONSES = {}
security_stub.auth_user = lambda: None
security_stub.bearer_scheme = None


async def _editor_dep(workspace_id: str | None = None):
    return None


security_stub.require_ws_editor = _editor_dep
sys.modules.setdefault("app.security", security_stub)

from app.core.db.session import get_db
from app.core.feature_flags import invalidate_cache
from app.domains.admin.infrastructure.models.feature_flag import FeatureFlag
from app.domains.nodes.application.node_service import NodeService
from app.domains.nodes.content_admin_router import router as nodes_router
from app.domains.workspaces.infrastructure.models import Workspace
from app.schemas.quest_validation import ValidationReport
from app.schemas.workspaces import WorkspaceSettings


async def _setup_app(monkeypatch, ws_features: dict[str, bool], system_flag: bool):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(FeatureFlag.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        ws = Workspace(
            id=uuid.uuid4(),
            name="W",
            slug="w",
            owner_user_id=uuid.uuid4(),
            settings_json=WorkspaceSettings(features=ws_features).model_dump(),
        )
        session.add(ws)
        if system_flag:
            session.add(FeatureFlag(key="ai.validation", value=True))
        await session.commit()
        workspace_id = ws.id

    invalidate_cache()

    app = FastAPI()
    app.include_router(nodes_router)

    async def override_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db

    async def fake_validate_with_ai(self, workspace_id, node_type, node_id):
        return ValidationReport(errors=0, warnings=0, items=[])

    monkeypatch.setattr(NodeService, "validate_with_ai", fake_validate_with_ai)

    return app, workspace_id


@pytest.mark.asyncio
async def test_validate_ai_disabled(monkeypatch):
    app, ws_id = await _setup_app(monkeypatch, {}, False)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            f"/admin/nodes/article/{uuid.uuid4()}/validate_ai",
            params={"workspace_id": str(ws_id)},
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_validate_ai_system_enabled_workspace_disabled(monkeypatch):
    app, ws_id = await _setup_app(monkeypatch, {}, True)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            f"/admin/nodes/article/{uuid.uuid4()}/validate_ai",
            params={"workspace_id": str(ws_id)},
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_validate_ai_enabled(monkeypatch):
    app, ws_id = await _setup_app(monkeypatch, {"ai.validation": True}, True)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            f"/admin/nodes/article/{uuid.uuid4()}/validate_ai",
            params={"workspace_id": str(ws_id)},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["report"] == {"errors": 0, "warnings": 0, "items": []}
    assert data["blocking"] == []
    assert data["warnings"] == []


@pytest.mark.asyncio
async def test_validate_ai_requires_editor(monkeypatch):
    async def forbidden(workspace_id: str | None = None):
        raise HTTPException(status_code=403, detail="forbidden")

    app, ws_id = await _setup_app(monkeypatch, {"ai.validation": True}, True)
    app.dependency_overrides[_editor_dep] = forbidden
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            f"/admin/nodes/article/{uuid.uuid4()}/validate_ai",
            params={"workspace_id": str(ws_id)},
        )
    assert resp.status_code == 403
