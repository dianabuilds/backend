from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.dao import NodeItemDAO
from app.domains.nodes.models import NodeItem
from app.domains.tags.models import ContentTag, Tag
from app.domains.workspaces.infrastructure.models import Workspace, WorkspaceMember
from app.schemas.workspaces import WorkspaceRole
from tests.conftest import test_engine


@pytest_asyncio.fixture
async def node_item_tables():
    async with test_engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(WorkspaceMember.__table__.create)
        await conn.run_sync(Tag.__table__.create)
        await conn.run_sync(NodeItem.__table__.create)
        await conn.run_sync(ContentTag.__table__.create)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(ContentTag.__table__.drop)
        await conn.run_sync(NodeItem.__table__.drop)
        await conn.run_sync(Tag.__table__.drop)
        await conn.run_sync(WorkspaceMember.__table__.drop)
        await conn.run_sync(Workspace.__table__.drop)


@pytest.mark.asyncio
async def test_node_item_crud(db_session: AsyncSession, node_item_tables, test_user):
    ws = Workspace(id=uuid4(), name="WS", slug="ws", owner_user_id=test_user.id)
    db_session.add(ws)
    db_session.add(
        WorkspaceMember(
            workspace_id=ws.id, user_id=test_user.id, role=WorkspaceRole.owner
        )
    )
    await db_session.commit()

    item = await NodeItemDAO.create(
        db_session,
        workspace_id=ws.id,
        type="article",
        slug="art1",
        title="Article 1",
    )
    await db_session.commit()
    assert item.id is not None

    items = await NodeItemDAO.list_by_type(
        db_session, workspace_id=ws.id, node_type="article"
    )
    assert len(items) == 1 and items[0].id == item.id

    search_items = await NodeItemDAO.search(
        db_session,
        workspace_id=ws.id,
        node_type="article",
        q="Article",
    )
    assert search_items and search_items[0].id == item.id

    tag = Tag(workspace_id=ws.id, slug="t1", name="Tag1")
    db_session.add(tag)
    await db_session.commit()

    ct = await NodeItemDAO.attach_tag(
        db_session, node_id=item.id, tag_id=tag.id, workspace_id=ws.id
    )
    await db_session.commit()
    assert ct.tag_id == tag.id

    await NodeItemDAO.detach_tag(db_session, node_id=item.id, tag_id=tag.id)
    await db_session.commit()

    res = await db_session.execute(
        select(ContentTag).where(ContentTag.content_id == item.id)
    )
    assert res.first() is None
