import importlib
import os
import sys
import types
import uuid

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Column
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Ensure app package is importable
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.api.admin.quests.steps import (  # noqa: E402
    admin_required,
    graph_router,
)
from app.api.admin.quests.steps import (  # noqa: E402
    router as steps_router,
)
from app.core.db.adapters import UUID as UUIDType  # noqa: E402
from app.core.db.session import get_db  # noqa: E402

# Minimal Base and Quest model to satisfy foreign key constraints
Base = declarative_base()
models_pkg = types.ModuleType("app.models")
models_pkg.Base = Base
models_pkg.__path__ = [os.path.join(os.getcwd(), "apps/backend/app/models")]
sys.modules.setdefault("app.models", models_pkg)

from app.models.quests import QuestStep, QuestStepTransition  # noqa: E402


class Quest(Base):
    __tablename__ = "quests"
    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)


@pytest_asyncio.fixture()
async def app_and_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Quest.__table__.create)
        await conn.run_sync(QuestStep.__table__.create)
        await conn.run_sync(QuestStepTransition.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    app = FastAPI()
    app.include_router(steps_router)
    app.include_router(graph_router)

    async def override_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db

    async def override_admin():
        return types.SimpleNamespace(id=uuid.uuid4(), role="admin")

    app.dependency_overrides[admin_required] = override_admin

    return app, async_session


@pytest.mark.asyncio
async def test_admin_quest_flow(app_and_session):
    app, async_session = app_and_session
    async with async_session() as session:
        quest = Quest()
        session.add(quest)
        await session.commit()
        quest_id = quest.id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/admin/quests/{quest_id}/steps",
            json={"key": "start", "title": "Start", "type": "start"},
        )
        assert resp.status_code == 201
        s1 = resp.json()

        resp = await client.post(
            f"/admin/quests/{quest_id}/steps",
            json={"key": "mid", "title": "Middle"},
        )
        assert resp.status_code == 201
        s2 = resp.json()

        resp = await client.post(
            f"/admin/quests/{quest_id}/steps",
            json={"key": "end", "title": "End", "type": "end"},
        )
        assert resp.status_code == 201
        s3 = resp.json()

        resp = await client.post(
            f"/admin/quests/{quest_id}/steps/{s1['id']}/transitions",
            json={"toStepId": s2["id"]},
        )
        assert resp.status_code == 201
        resp = await client.post(
            f"/admin/quests/{quest_id}/steps/{s2['id']}/transitions",
            json={"toStepId": s3["id"]},
        )
        assert resp.status_code == 201

        resp = await client.get(f"/admin/quests/{quest_id}/graph")
        assert resp.status_code == 200
        graph = resp.json()
        assert len(graph["steps"]) == 3
        assert len(graph["transitions"]) == 2

        resp = await client.delete(f"/admin/quests/{quest_id}/steps/{s2['id']}")
        assert resp.status_code == 200

        resp = await client.get(f"/admin/quests/{quest_id}/graph")
        assert resp.status_code == 200
        graph = resp.json()
        assert len(graph["steps"]) == 2
        assert len(graph["transitions"]) == 0
        keys = [s["key"] for s in graph["steps"]]
        assert keys == ["start", "end"]
