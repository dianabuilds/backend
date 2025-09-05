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

from app.domains.navigation.api import admin_traces_router
from app.providers.db.session import get_db


@pytest_asyncio.fixture
async def traces_client(db_session: AsyncSession) -> AsyncClient:
    app = FastAPI()
    app.include_router(admin_traces_router.router)

    async def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[admin_traces_router.admin_required] = lambda: types.SimpleNamespace(
        id=uuid4()
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def _prepare_traces(db: AsyncSession) -> None:
    await db.execute(text("DROP TABLE IF EXISTS node_traces"))
    await db.execute(text("DROP TABLE IF EXISTS nodes"))
    await db.execute(text("CREATE TABLE nodes (id INTEGER PRIMARY KEY, slug TEXT NOT NULL)"))
    await db.execute(
        text(
            "CREATE TABLE node_traces ("
            "id TEXT PRIMARY KEY,"
            "node_id INTEGER NOT NULL,"
            "to_node_id INTEGER,"
            "user_id TEXT,"
            "type TEXT,"
            "created_at TIMESTAMP"
            ")"
        )
    )
    await db.execute(text("INSERT INTO nodes (id, slug) VALUES (1, 'start'), (2, 'end')"))
    await db.execute(
        text(
            "INSERT INTO node_traces (id, node_id, to_node_id, type, created_at) "
            "VALUES (:id, 1, 2, 'manual', :dt)"
        ),
        {"id": str(uuid4()), "dt": datetime.utcnow()},
    )
    await db.commit()


@pytest.mark.asyncio
async def test_list_traces_success(traces_client: AsyncClient, db_session: AsyncSession) -> None:
    await _prepare_traces(db_session)
    resp = await traces_client.get("/admin/traces")
    assert resp.status_code == 200
    data = resp.json()
    assert data[0]["from_slug"] == "start"
    assert data[0]["to_slug"] == "end"
    assert "type" in data[0]


@pytest.mark.asyncio
async def test_list_traces_unknown_column(
    traces_client: AsyncClient, db_session: AsyncSession
) -> None:
    await _prepare_traces(db_session)
    resp = await traces_client.get("/admin/traces?source=test")
    assert resp.status_code == 400
    assert "source" in resp.json()["detail"]
