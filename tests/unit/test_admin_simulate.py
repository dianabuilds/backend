import sys
import uuid
import asyncio
import importlib
from pathlib import Path
from types import SimpleNamespace

# Ensure apps package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.modules.setdefault("app", importlib.import_module("apps.backend.app"))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.db.base import Base
from app.domains.navigation.api.admin_transitions_simulate import (
    SimulateRequest,
    simulate_transitions,
)
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.users.infrastructure.models.user import User
from app.domains.workspaces.infrastructure.models import Workspace


def test_simulate_endpoint_returns_trace():
    async def _run():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            user = User(id=uuid.uuid4())
            ws = Workspace(id=uuid.uuid4(), name="W", slug="w", owner_user_id=user.id)
            node = Node(workspace_id=ws.id, slug="start", content={}, author_id=user.id)
            session.add_all([user, ws, node])
            await session.commit()

            payload = SimulateRequest(start="start", seed=1, preview_mode="dry_run")
            res = await simulate_transitions(
                payload,
                SimpleNamespace(id=uuid.uuid4(), role="admin"),
                session,
            )
            assert "trace" in res
            assert isinstance(res["trace"], list)

    asyncio.run(_run())
