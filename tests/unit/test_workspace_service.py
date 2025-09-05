from __future__ import annotations

import importlib
import sys
import types
import uuid
from dataclasses import dataclass

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Ensure app package is importable
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

# Minimal security stub to satisfy imports
security_stub = types.ModuleType("app.security")
security_stub.ADMIN_AUTH_RESPONSES = {}
security_stub.auth_user = lambda: None
security_stub.require_ws_editor = lambda *a, **k: None
security_stub.require_ws_owner = lambda *a, **k: None
security_stub.require_ws_viewer = lambda *a, **k: None
sys.modules.setdefault("app.security", security_stub)

from app.domains.workspaces.application.service import WorkspaceService  # noqa: E402
from app.domains.workspaces.infrastructure.models import (  # noqa: E402
    Workspace,
    WorkspaceMember,
)
from app.schemas.workspaces import WorkspaceRole, WorkspaceSettings  # noqa: E402


@dataclass
class DummyUser:
    id: uuid.UUID
    role: str = "user"


@pytest.mark.asyncio
async def test_list_for_user_returns_workspaces_with_roles() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(WorkspaceMember.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    uid = uuid.uuid4()
    async with async_session() as session:
        user = DummyUser(id=uid)
        ws1 = Workspace(id=1, name="W1", slug="w1", owner_user_id=uid)
        ws2 = Workspace(id=2, name="W2", slug="w2", owner_user_id=uid)
        session.add_all([ws1, ws2])
        session.add_all(
            [
                WorkspaceMember(workspace_id=ws1.id, user_id=uid, role=WorkspaceRole.owner),
                WorkspaceMember(workspace_id=ws2.id, user_id=uid, role=WorkspaceRole.viewer),
            ]
        )
        await session.commit()

        rows = await WorkspaceService.list_for_user(session, user)
        assert len(rows) == 2


@pytest.mark.asyncio
async def test_get_ai_presets_returns_presets() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(WorkspaceMember.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        ws = Workspace(
            id=1,
            name="W",
            slug="w",
            owner_user_id=uuid.uuid4(),
            settings_json=WorkspaceSettings(ai_presets={"foo": "bar"}).model_dump(),
        )
        session.add(ws)
        await session.commit()

        presets = await WorkspaceService.get_ai_presets(session, ws.id)
        assert presets == {"foo": "bar"}


@pytest.mark.asyncio
async def test_get_ai_presets_not_found() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(WorkspaceMember.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        with pytest.raises(HTTPException) as exc:
            await WorkspaceService.get_ai_presets(session, 123)
        assert exc.value.status_code == 404
