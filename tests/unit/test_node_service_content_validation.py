import sys
import uuid
from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps/backend"))

from app.domains.nodes.application.node_service import NodeService
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.models import NodeItem, NodePatch
from app.domains.workspaces.infrastructure.models import Workspace
from app.schemas.nodes_common import Status, Visibility


@pytest.mark.asyncio
async def test_update_rejects_legacy_nodes_field() -> None:
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

        service = NodeService(session)
        with pytest.raises(HTTPException) as exc:
            await service.update(workspace_id, item.id, {"nodes": {}}, actor_id=actor_id)
        assert exc.value.status_code == 422
        assert exc.value.detail == "Field 'nodes' is deprecated; use 'content' instead"
