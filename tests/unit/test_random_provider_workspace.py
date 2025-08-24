import importlib
import sys
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

import asyncio
import types

# Ensure apps package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.modules.setdefault("app", importlib.import_module("apps.backend.app"))
stub = types.ModuleType("nft_service")

async def _user_has_nft(user, nft):
    return False

stub.user_has_nft = _user_has_nft
sys.modules.setdefault("app.domains.users.application.nft_service", stub)

from app.core.db.base import Base  # noqa: E402
from app.domains.navigation.application.transition_router import (  # noqa: E402
    RandomProvider,
)
from app.domains.nodes.infrastructure.models.node import Node  # noqa: E402
from app.domains.users.infrastructure.models.user import User  # noqa: E402
from app.domains.workspaces.infrastructure.models import Workspace  # noqa: E402


def test_random_provider_scoped_by_workspace() -> None:
    async def _run() -> None:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            user = User(id=uuid.uuid4())
            w1 = Workspace(id=uuid.uuid4(), name="W1", slug="w1", owner_user_id=user.id)
            w2 = Workspace(id=uuid.uuid4(), name="W2", slug="w2", owner_user_id=user.id)
            start = Node(
                workspace_id=w1.id,
                content={},
                author_id=user.id,
                is_visible=True,
                is_public=True,
                is_recommendable=True,
            )
            n1 = Node(
                workspace_id=w1.id,
                content={},
                author_id=user.id,
                is_visible=True,
                is_public=True,
                is_recommendable=True,
            )
            n2 = Node(
                workspace_id=w2.id,
                content={},
                author_id=user.id,
                is_visible=True,
                is_public=True,
                is_recommendable=True,
            )
            session.add_all([user, w1, w2, start, n1, n2])
            await session.commit()

            provider = RandomProvider(seed=42)
            res = await provider.get_transitions(session, start, None, w1.id)
            assert all(n.workspace_id == w1.id for n in res)

    asyncio.run(_run())

