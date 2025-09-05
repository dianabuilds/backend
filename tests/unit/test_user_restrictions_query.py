import importlib
import sys
import types
import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request

# Ensure app package resolves
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

ws_stub = types.ModuleType("app.domains.workspaces.application.service")
ws_stub.WorkspaceService = type("WorkspaceService", (), {})
ws_stub.require_ws_editor = lambda *args, **kwargs: None
ws_stub.require_ws_guest = lambda *args, **kwargs: None
ws_stub.require_ws_owner = lambda *args, **kwargs: None
ws_stub.require_ws_viewer = lambda *args, **kwargs: None
sys.modules.setdefault("app.domains.workspaces.application.service", ws_stub)

from app.api import deps  # noqa: E402
from app.core.preview import PreviewContext  # noqa: E402
from app.domains.moderation.infrastructure.models.moderation_models import (  # noqa: E402
    UserRestriction,
)
from app.domains.users.infrastructure.models.user import User  # noqa: E402


@pytest.mark.asyncio
async def test_get_current_user_fetches_restrictions_once(monkeypatch):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(UserRestriction.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    uid = uuid.uuid4()
    async with async_session() as session:
        session.add(
            User(
                id=uid,
                email="e@e",
                username="u",
                is_active=True,
            )
        )
        session.add(UserRestriction(user_id=uid, type="post_restrict"))
        await session.commit()

    async with async_session() as session:
        token = "token"
        monkeypatch.setattr(deps, "verify_access_token", lambda _: str(uid))
        scope = {
            "type": "http",
            "headers": [(b"cookie", f"access_token={token}".encode())],
        }
        req = Request(scope)
        statements: list[str] = []

        def count_sql(conn, cursor, statement, parameters, context, executemany):  # noqa: ANN001
            if statement.startswith("SELECT"):
                statements.append(statement)

        event.listen(engine.sync_engine, "before_cursor_execute", count_sql)
        try:
            user = await deps.get_current_user(req, None, session, PreviewContext())
            with pytest.raises(HTTPException):
                await deps.ensure_can_post(user)
        finally:
            event.remove(engine.sync_engine, "before_cursor_execute", count_sql)

    assert len(statements) == 1
    assert "post_restrict" in user.active_restrictions
