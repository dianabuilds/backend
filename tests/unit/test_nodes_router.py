from __future__ import annotations

import os
import pathlib
import sys
import uuid
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "apps/backend"))
os.environ.setdefault("TESTING", "true")

from app.domains.accounts.infrastructure.models import Account
from app.domains.nodes.api.nodes_router import read_node
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.users.infrastructure.models.user import User


@pytest_asyncio.fixture()
async def db() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(User.__table__.create)
        await conn.run_sync(Account.__table__.create)
        await conn.run_sync(Node.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_read_node_no_commit(monkeypatch: pytest.MonkeyPatch, db: AsyncSession) -> None:
    user_id = uuid.uuid4()
    user = User(id=user_id)
    account = Account(name="A", slug="a", owner_user_id=user_id)
    db.add_all([user, account])
    await db.commit()

    node = Node(account_id=account.id, slug="n1", author_id=user_id, is_visible=True)
    db.add(node)
    await db.commit()

    async def _require_ws_guest(account_id: int, user: User, db: AsyncSession) -> None:
        return None

    async def _noop_trace(
        self, db: AsyncSession, node: Node, user: User, chance: float = 0.3
    ) -> None:
        return None

    monkeypatch.setattr("app.domains.nodes.api.nodes_router.require_ws_guest", _require_ws_guest)
    monkeypatch.setattr(
        "app.domains.navigation.application.traces_service.TracesService.maybe_add_auto_trace",
        _noop_trace,
    )

    commit_mock = AsyncMock()
    monkeypatch.setattr(db, "commit", commit_mock)

    scope = {"type": "http", "headers": []}
    request = Request(scope)
    request.state.account_id = account.id
    response = Response()

    result = await read_node(request, node.slug, response, None, user, db, object())
    assert result.views == 1
    commit_mock.assert_not_awaited()
