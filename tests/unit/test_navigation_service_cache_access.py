from __future__ import annotations

import importlib
import sys
import uuid
from types import SimpleNamespace

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Ensure app package resolves
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.domains.navigation.application.navigation_service import (  # noqa: E402
    NavigationService,
)
from app.domains.nodes.infrastructure.models.node import Node  # noqa: E402
from app.domains.quests.infrastructure.models.navigation_cache_models import (  # noqa: E402
    NavigationCache,
)
from app.domains.tags.infrastructure.models.tag_models import NodeTag  # noqa: E402
from app.domains.tags.models import Tag  # noqa: E402
from app.domains.workspaces.infrastructure.models import Workspace  # noqa: E402


@pytest.mark.asyncio
async def test_navigation_service_filters_cached_transitions():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(Tag.__table__.create)
        await conn.run_sync(Node.__table__.create)
        await conn.run_sync(NodeTag.__table__.create)
        await conn.run_sync(NavigationCache.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        ws_id = uuid.uuid4()
        ws = Workspace(id=ws_id, name="W", slug="w", owner_user_id=uuid.uuid4())
        session.add(ws)
        start = Node(
            id=1,
            account_id=ws_id,
            slug="start",
            title="Start",
            content={},
            media=[],
            author_id=uuid.uuid4(),
            is_visible=True,
            is_public=True,
            premium_only=False,
            is_recommendable=True,
        )
        open_node = Node(
            id=2,
            account_id=ws_id,
            slug="open",
            title="Open",
            content={},
            media=[],
            author_id=uuid.uuid4(),
            is_visible=True,
            is_public=True,
            premium_only=False,
            is_recommendable=True,
        )
        private_node = Node(
            id=3,
            account_id=ws_id,
            slug="priv",
            title="Priv",
            content={},
            media=[],
            author_id=uuid.uuid4(),
            is_visible=True,
            is_public=False,
            premium_only=False,
            is_recommendable=True,
        )
        premium_node = Node(
            id=4,
            account_id=ws_id,
            slug="prem",
            title="Prem",
            content={},
            media=[],
            author_id=uuid.uuid4(),
            is_visible=True,
            is_public=True,
            premium_only=False,
            is_recommendable=True,
        )
        session.add_all([start, open_node, private_node, premium_node])
        nav = {
            "mode": "auto",
            "transitions": [
                {"slug": "open", "id": "t1"},
                {"slug": "priv", "id": "t2"},
                {
                    "slug": "prem",
                    "id": "t3",
                    "condition": {"premium_required": True},
                },
            ],
        }
        session.add(NavigationCache(node_slug="start", navigation=nav, compass=[], echo=[]))
        await session.commit()

        user = SimpleNamespace(is_premium=False, premium_until=None)
        svc = NavigationService()
        transitions = await svc.generate_transitions(session, start, user)
        assert [t["slug"] for t in transitions] == ["open"]

        navigation = await svc.get_navigation(session, start, user)
        assert [t["slug"] for t in navigation["transitions"]] == ["open"]
