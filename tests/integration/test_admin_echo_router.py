from __future__ import annotations

import types
from datetime import datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.navigation.api import admin_echo_router
from app.providers.db.session import get_db


@pytest_asyncio.fixture
async def echo_client(db_session: AsyncSession) -> AsyncClient:
    app = FastAPI()
    app.include_router(admin_echo_router.router)

    async def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[admin_echo_router.admin_required] = lambda: types.SimpleNamespace(
        id=uuid4()
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def _prepare_echo(db: AsyncSession) -> None:
    await db.execute(text("DROP TABLE IF EXISTS echo_trace"))
    await db.execute(text("DROP TABLE IF EXISTS nodes"))
    await db.execute(text("CREATE TABLE nodes (id INTEGER PRIMARY KEY, slug TEXT NOT NULL)"))
    await db.execute(
        text(
            "CREATE TABLE echo_trace ("
            "id TEXT PRIMARY KEY, "
            "from_node_id TEXT, "
            "to_node_id TEXT, "
            "user_id TEXT, "
            "created_at TIMESTAMP)"
        )
    )
    await db.execute(text("INSERT INTO nodes (id, slug) VALUES (1, 'start'), (2, 'end')"))
    await db.execute(
        text(
            "INSERT INTO echo_trace (id, from_node_id, to_node_id, created_at) "
            "VALUES (:id, '1', '2', :dt)"
        ),
        {"id": str(uuid4()), "dt": datetime.utcnow()},
    )
    await db.commit()


@pytest.mark.asyncio
async def test_list_echo_traces_success(echo_client: AsyncClient, db_session: AsyncSession) -> None:
    await _prepare_echo(db_session)
    resp = await echo_client.get("/admin/echo")
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["from_slug"] == "start"
    assert data[0]["to_slug"] == "end"
