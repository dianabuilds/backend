from __future__ import annotations

import importlib
import sys
import uuid
from types import SimpleNamespace

import pytest
import sqlalchemy as sa
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request

# Ensure "app" package resolves correctly
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.api.workspace_context import (  # noqa: E402
    get_workspace_id,
    optional_workspace,
    require_workspace,
    resolve_workspace,
)
from app.domains.quests.infrastructure.models import quest_models  # noqa: F401, E402
from app.domains.users.infrastructure.models.user import User  # noqa: E402
from app.domains.workspaces.infrastructure.models import (  # noqa: E402
    Workspace,
    WorkspaceMember,
)


def _make_request(headers=None, query_string: bytes = b"") -> Request:
    headers = headers or []
    scope = {"type": "http", "headers": headers, "query_string": query_string}
    return Request(scope)


def test_get_workspace_id_from_header() -> None:
    wid = 123
    req = _make_request([(b"x-workspace-id", str(wid).encode())])
    assert get_workspace_id(req) == wid


def test_get_workspace_id_from_query() -> None:
    wid = 456
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
        ws = Workspace(id=1, name="W", slug="w", owner_user_id=user_id)
        session.add(ws)
        await session.commit()

        user = SimpleNamespace(id=user_id, role="user")
        with pytest.raises(HTTPException) as exc:
            await resolve_workspace(ws.id, user=user, db=session)
        assert exc.value.status_code == 403

        admin = SimpleNamespace(id=user_id, role="admin")
        w = await resolve_workspace(ws.id, user=admin, db=session)
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
        ws = Workspace(id=1, name="W", slug="w", owner_user_id=user_id)
        session.add(ws)
        await session.commit()

        req = _make_request([(b"x-workspace-id", str(ws.id).encode())])
        admin = SimpleNamespace(id=user_id, role="admin")
        w = await require_workspace(request=req, user=admin, db=session)
        assert w.id == ws.id
        assert req.state.workspace_id == str(ws.id)
        assert req.state.workspace is w


@pytest.mark.asyncio
async def test_optional_workspace_without_id_errors() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        req = _make_request()
        user = SimpleNamespace(id=uuid.uuid4(), role="user")
        with pytest.raises(HTTPException) as exc:
            await optional_workspace(request=req, user=user, db=session)
        assert exc.value.status_code == 400


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
        ws = Workspace(id=1, name="W", slug="w", owner_user_id=uuid.uuid4())
        session.add(ws)
        await session.commit()

        admin_user = SimpleNamespace(id=uuid.uuid4(), role="admin")
        w = await resolve_workspace(ws.id, user=admin_user, db=session)
        assert w.id == ws.id
