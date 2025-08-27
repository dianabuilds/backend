from pathlib import Path
import sys
import importlib
import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import sqlalchemy as sa

# Ensure "app" package resolves correctly
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.domains.workspaces.infrastructure.models import Workspace, WorkspaceMember
from app.domains.users.infrastructure.models.user import User
from app.schemas.workspaces import WorkspaceRole
from app.core.workspace_context import (
    get_workspace_id,
    resolve_workspace,
    require_workspace,
    optional_workspace,
)


def _make_request(headers=None, query_string: bytes = b"") -> Request:
    headers = headers or []
    scope = {"type": "http", "headers": headers, "query_string": query_string}
    return Request(scope)


def test_get_workspace_id_from_header() -> None:
    wid = uuid.uuid4()
    req = _make_request([(b"x-workspace-id", str(wid).encode())])
    assert get_workspace_id(req) == wid


def test_get_workspace_id_from_query() -> None:
    wid = uuid.uuid4()
    req = _make_request(query_string=f"workspace_id={wid}".encode())
    assert get_workspace_id(req) == wid


@pytest.mark.asyncio
async def test_resolve_workspace_checks_membership() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(WorkspaceMember.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        user_id = uuid.uuid4()
        ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user_id)
        session.add(ws)
        await session.commit()

        user = SimpleNamespace(id=user_id, role="user")
        with pytest.raises(HTTPException):
            await resolve_workspace(ws.id, user=user, db=session)

        member = WorkspaceMember(workspace_id=ws.id, user_id=user_id, role=WorkspaceRole.viewer)
        session.add(member)
        await session.commit()

        w = await resolve_workspace(ws.id, user=user, db=session)
        assert w.id == ws.id


@pytest.mark.asyncio
async def test_require_workspace_sets_state() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(WorkspaceMember.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        user_id = uuid.uuid4()
        await session.execute(sa.insert(User.__table__).values(id=user_id))
        ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user_id)
        session.add(ws)
        member = WorkspaceMember(workspace_id=ws.id, user_id=user_id, role=WorkspaceRole.viewer)
        session.add(member)
        await session.commit()

        req = _make_request([(b"x-workspace-id", str(ws.id).encode())])
        user = SimpleNamespace(id=user_id, role="user")
        w = await require_workspace(request=req, user=user, db=session)
        assert w.id == ws.id
        assert req.state.workspace_id == str(ws.id)
        assert req.state.workspace is w


@pytest.mark.asyncio
async def test_optional_workspace_no_id_returns_none() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        req = _make_request()
        user = SimpleNamespace(id=uuid.uuid4(), role="user")
        res = await optional_workspace(request=req, user=user, db=session)
        assert res is None
        assert not hasattr(req.state, "workspace")


def test_get_workspace_id_invalid_uuid() -> None:
    """An invalid workspace id in header should raise an error."""
    req = _make_request([(b"x-workspace-id", b"not-a-uuid")])
    with pytest.raises(HTTPException) as exc:
        get_workspace_id(req)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_require_workspace_without_id_errors() -> None:
    """require_workspace should error when no workspace id provided."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(WorkspaceMember.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        user = SimpleNamespace(id=uuid.uuid4(), role="user")
        req = _make_request()
        with pytest.raises(HTTPException) as exc:
            await require_workspace(request=req, user=user, db=session)
        assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_resolve_workspace_allows_admin_without_membership() -> None:
    """Admin users can resolve workspaces without membership."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(Workspace.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=uuid.uuid4())
        session.add(ws)
        await session.commit()

        admin_user = SimpleNamespace(id=uuid.uuid4(), role="admin")
        w = await resolve_workspace(ws.id, user=admin_user, db=session)
        assert w.id == ws.id
