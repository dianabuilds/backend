from __future__ import annotations

import asyncio
import importlib
import random
import sys
import uuid
from dataclasses import dataclass
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Ensure apps package is importable
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

# Stub NFT service dependency missing in tests
import types  # noqa: E402

sys.modules.setdefault(
    "app.domains.users.application.nft_service",
    types.SimpleNamespace(user_has_nft=lambda *args, **kwargs: False),
)

from apps.backend.app.domains.navigation.application.router import (  # noqa: E402
    TransitionResult,
    TransitionTrace,
)

from app.core.preview import PreviewContext  # noqa: E402
from app.domains.achievements.infrastructure.models.achievement_models import (  # noqa: E402
    UserAchievement,
)
from app.domains.navigation.api import preview_router  # noqa: E402
from app.domains.navigation.api.preview_router import (  # noqa: E402
    SimulateRequest,
    simulate_transitions,
)
from app.domains.nodes.infrastructure.models.node import Node  # noqa: E402
from app.domains.tags.infrastructure.models.tag_models import NodeTag  # noqa: E402
from app.domains.tags.models import Tag  # noqa: E402
from app.domains.users.infrastructure.models.user import User  # noqa: E402
from app.domains.workspaces.infrastructure.models import Workspace  # noqa: E402
from app.models.event_counter import UserEventCounter  # noqa: E402
from app.providers.db.base import Base  # noqa: E402


@dataclass
class DummyNode:
    slug: str
    workspace_id: uuid.UUID | None = None


class DummyRouter:
    def __init__(self) -> None:
        self.history: list[str] = []

    async def route(self, db, start, user, budget, preview: PreviewContext | None = None):
        rng = random.Random(preview.seed if preview else None)
        options = ["n1", "n2"]
        chosen = rng.choice(options)
        if not preview or preview.mode == "off":
            self.history.append(chosen)
        trace = [TransitionTrace(options, [], chosen)]
        return TransitionResult(next=DummyNode(chosen), reason=None, trace=trace, metrics={})


class DummyNavigationService:
    last_instance: DummyNavigationService | None = None

    def __init__(self) -> None:
        self._router = DummyRouter()
        DummyNavigationService.last_instance = self

    async def build_route(self, db, node, user, preview: PreviewContext | None = None, mode=None):
        budget = SimpleNamespace(
            max_time_ms=1000, max_queries=1000, max_filters=1000, fallback_chain=[]
        )
        return await self._router.route(db, node, user, budget, preview=preview)

    async def get_next(self, db, node, user, preview: PreviewContext | None = None, mode=None):
        return await self.build_route(db, node, user, preview=preview, mode=mode)


def test_dry_run_seed_and_no_side_effects(monkeypatch):
    async def _run():
        monkeypatch.setattr(preview_router, "NavigationService", DummyNavigationService)

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Workspace.__table__.create)
            await conn.run_sync(User.__table__.create)
            await conn.run_sync(Node.__table__.create)
            await conn.run_sync(Tag.__table__.create)
            await conn.run_sync(NodeTag.__table__.create)
            await conn.run_sync(UserEventCounter.__table__.create)
            await conn.run_sync(UserAchievement.__table__.create)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            user = User(id=uuid.uuid4())
            ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user.id)
            node = Node(
                id=1,
                account_id=ws.id,
                slug="start",
                content={},
                author_id=user.id,
            )
            counter = UserEventCounter(workspace_id=ws.id, user_id=user.id, event="evt", count=0)
            session.add_all([user, ws, node, counter])
            await session.commit()

            payload = SimulateRequest(
                workspace_id=ws.id,
                start="start",
                seed=1,
                preview_mode="dry_run",
            )
            res1 = await simulate_transitions(payload, session)
            res2 = await simulate_transitions(payload, session)
            res3 = await simulate_transitions(
                SimulateRequest(
                    workspace_id=ws.id,
                    start="start",
                    seed=5,
                    preview_mode="dry_run",
                ),
                session,
            )

            assert res1["trace"] == res2["trace"]
            assert res1["trace"] != res3["trace"]

            await session.refresh(counter)
            assert counter.count == 0
            uas = (await session.execute(UserAchievement.__table__.select())).fetchall()
            assert len(uas) == 0

    asyncio.run(_run())


def test_preview_link_endpoint_accessible(monkeypatch):
    monkeypatch.setenv("DATABASE__USERNAME", "x")
    monkeypatch.setenv("DATABASE__PASSWORD", "x")
    monkeypatch.setenv("DATABASE__HOST", "x")
    monkeypatch.setenv("DATABASE__NAME", "x")

    from app.domains.navigation.api.preview_router import router as preview_router

    app = FastAPI()
    app.include_router(preview_router)

    admin_dep = None
    for route in preview_router.routes:
        if route.path == "/admin/preview/link":
            admin_dep = route.dependant.dependencies[0].call
            break
    assert admin_dep is not None
    app.dependency_overrides[admin_dep] = lambda: None

    client = TestClient(app)
    ws_id = str(uuid.uuid4())
    res = client.post("/admin/preview/link", json={"workspace_id": ws_id})
    assert res.status_code == 200
    assert "url" in res.json()

    res_get = client.get("/admin/preview/link", params={"workspace_id": ws_id})
    assert res_get.status_code == 200
    assert "url" in res_get.json()


def test_read_only_renders_route_without_transition(monkeypatch):
    async def _run():
        monkeypatch.setattr(preview_router, "NavigationService", DummyNavigationService)

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Workspace.__table__.create)
            await conn.run_sync(User.__table__.create)
            await conn.run_sync(Node.__table__.create)
            await conn.run_sync(Tag.__table__.create)
            await conn.run_sync(NodeTag.__table__.create)
            await conn.run_sync(UserEventCounter.__table__.create)
            await conn.run_sync(UserAchievement.__table__.create)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            user = User(id=uuid.uuid4())
            ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user.id)
            node = Node(
                id=1,
                account_id=ws.id,
                slug="start",
                content={},
                author_id=user.id,
            )
            session.add_all([user, ws, node])
            await session.commit()

            payload = SimulateRequest(
                workspace_id=ws.id,
                start="start",
                seed=1,
                preview_mode="read_only",
            )
            res = await simulate_transitions(payload, session)
            assert res["next"] in {"n1", "n2"}
            svc = DummyNavigationService.last_instance
            assert svc is not None
            assert svc._router.history == []

    asyncio.run(_run())


def test_preview_token_workspace_validation(monkeypatch):
    async def _run():
        monkeypatch.setattr(preview_router, "NavigationService", DummyNavigationService)

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Workspace.__table__.create)
            await conn.run_sync(User.__table__.create)
            await conn.run_sync(Node.__table__.create)
            await conn.run_sync(Tag.__table__.create)
            await conn.run_sync(NodeTag.__table__.create)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            user = User(id=uuid.uuid4())
            ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user.id)
            node = Node(
                id=1,
                account_id=ws.id,
                slug="start",
                content={},
                author_id=user.id,
            )
            session.add_all([user, ws, node])
            await session.commit()

            payload = SimulateRequest(workspace_id=ws.id, start="start")
            req = SimpleNamespace(state=SimpleNamespace(preview_token={"workspace_id": str(ws.id)}))
            res = await simulate_transitions(payload, session, req)
            assert res["next"] in {"n1", "n2"}

            bad_req = SimpleNamespace(
                state=SimpleNamespace(preview_token={"workspace_id": str(uuid.uuid4())})
            )
            with pytest.raises(HTTPException):
                await simulate_transitions(payload, session, bad_req)

    asyncio.run(_run())


def test_returns_seed_for_replay(monkeypatch):
    async def _run():
        monkeypatch.setattr(preview_router, "NavigationService", DummyNavigationService)

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            user = User(id=uuid.uuid4())
            ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user.id)
            node = Node(
                id=uuid.uuid4(),
                account_id=ws.id,
                slug="start",
                content={},
                author_id=user.id,
            )
            session.add_all([user, ws, node])
            await session.commit()

            payload = SimulateRequest(
                workspace_id=ws.id,
                start="start",
                preview_mode="dry_run",
            )
            res1 = await simulate_transitions(payload, session)
            seed = res1["seed"]
            res2 = await simulate_transitions(
                SimulateRequest(
                    workspace_id=ws.id,
                    start="start",
                    preview_mode="dry_run",
                    seed=seed,
                ),
                session,
            )
            assert res1["trace"] == res2["trace"]

    asyncio.run(_run())
