from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps/backend"))

from app.domains.nodes.application.node_service import NodeService
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.models import NodeItem, NodePatch
from app.domains.workspaces.infrastructure.models import Workspace
from app.schemas.nodes_common import Status, Visibility


@pytest.mark.asyncio
async def test_update_accepts_content_field() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(Node.__table__.create)
        await conn.run_sync(NodeItem.__table__.create)
        await conn.run_sync(NodePatch.__table__.create)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        workspace_id = uuid.uuid4()
        actor_id = uuid.uuid4()
        node = Node(
            id=1,
            workspace_id=workspace_id,
            slug="n1",
            title="N1",
            author_id=actor_id,
            status=Status.draft,
            visibility=Visibility.private,
            created_by_user_id=actor_id,
            updated_by_user_id=actor_id,
        )
        item = NodeItem(
            id=1,
            node_id=node.id,
            workspace_id=workspace_id,
            type="quest",
            slug="n1",
            title="N1",
            status=Status.draft,
            created_by_user_id=actor_id,
        )
        session.add_all([node, item])
        await session.commit()

        import app.domains.nodes.application.node_service as ns

        class _DummyNavSvc:
            async def invalidate_navigation_cache(self, *args, **kwargs) -> None:  # noqa: ANN002
                return None

        class _DummyNavCache:
            async def invalidate_navigation_by_node(self, *args, **kwargs) -> None:  # noqa: ANN002
                return None

            async def invalidate_modes_by_node(self, *args, **kwargs) -> None:  # noqa: ANN002
                return None

            async def invalidate_compass_all(self) -> None:  # noqa: D401
                return None

        ns.navsvc = _DummyNavSvc()
        ns.navcache = _DummyNavCache()

        service = NodeService(session)
        await service.update(
            workspace_id,
            item.id,
            {"content": {"time": 0, "blocks": [], "version": "2.30.7"}},
            actor_id=actor_id,
        )
        await session.refresh(node)
        assert node.content == {"time": 0, "blocks": [], "version": "2.30.7"}
