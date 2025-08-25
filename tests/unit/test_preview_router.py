import asyncio
import importlib
import random
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Ensure apps package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

# Stub NFT service dependency missing in tests
import types  # noqa: E402

sys.modules.setdefault(
    "app.domains.users.application.nft_service",
    types.SimpleNamespace(user_has_nft=lambda *args, **kwargs: False),
)

from apps.backend.app.domains.navigation.application.transition_router import (  # noqa: E402
    TransitionResult,
    TransitionTrace,
)

from app.core.db.base import Base  # noqa: E402
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
from app.domains.users.infrastructure.models.user import User  # noqa: E402
from app.domains.workspaces.infrastructure.models import Workspace  # noqa: E402
from app.models.event_counter import UserEventCounter  # noqa: E402


@dataclass
class DummyNode:
    slug: str
    workspace_id: uuid.UUID | None = None


class DummyRouter:
    def __init__(self) -> None:
        self.history: list[str] = []

    async def route(
        self, db, start, user, budget, preview: Optional[PreviewContext] = None
    ):
        rng = random.Random(preview.seed if preview else None)
        options = ["n1", "n2"]
        chosen = rng.choice(options)
        if not preview or preview.mode == "off":
            self.history.append(chosen)
        trace = [TransitionTrace(options, [], {}, chosen)]
        return TransitionResult(
            next=DummyNode(chosen), reason=None, trace=trace, metrics={}
        )


class DummyNavigationService:
    last_instance: Optional["DummyNavigationService"] = None

    def __init__(self) -> None:
        self._router = DummyRouter()
        DummyNavigationService.last_instance = self

    async def build_route(self, db, node, user, preview=None):
        budget = SimpleNamespace(
            max_time_ms=1000, max_queries=1000, max_filters=1000, fallback_chain=[]
        )
        return await self._router.route(db, node, user, budget, preview=preview)


def test_dry_run_seed_and_no_side_effects(monkeypatch):
    async def _run():
        monkeypatch.setattr(preview_router, "NavigationService", DummyNavigationService)

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            user = User(id=uuid.uuid4())
            ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user.id)
            node = Node(workspace_id=ws.id, slug="start", content={}, author_id=user.id)
            counter = UserEventCounter(
                workspace_id=ws.id, user_id=user.id, event="evt", count=0
            )
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


def test_read_only_renders_route_without_transition(monkeypatch):
    async def _run():
        monkeypatch.setattr(preview_router, "NavigationService", DummyNavigationService)

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            user = User(id=uuid.uuid4())
            ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user.id)
            node = Node(workspace_id=ws.id, slug="start", content={}, author_id=user.id)
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
            await conn.run_sync(Base.metadata.create_all)
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            user = User(id=uuid.uuid4())
            ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user.id)
            node = Node(workspace_id=ws.id, slug="start", content={}, author_id=user.id)
            session.add_all([user, ws, node])
            await session.commit()

            payload = SimulateRequest(workspace_id=ws.id, start="start")
            req = SimpleNamespace(
                state=SimpleNamespace(preview_token={"workspace_id": str(ws.id)})
            )
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
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            user = User(id=uuid.uuid4())
            ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user.id)
            node = Node(workspace_id=ws.id, slug="start", content={}, author_id=user.id)
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
