import pytest
import pytest_asyncio
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from tests.conftest import test_engine
from app.domains.workspaces.infrastructure.models import Workspace
from app.domains.workspaces.infrastructure.models import WorkspaceMember
from app.domains.content.models import ContentItem
from app.domains.tags.models import Tag, ContentTag
from app.domains.content.dao import ContentItemDAO
from app.schemas.workspaces import WorkspaceRole


@pytest_asyncio.fixture
async def content_tables():
    async with test_engine.begin() as conn:
        await conn.run_sync(Workspace.__table__.create)
        await conn.run_sync(WorkspaceMember.__table__.create)
        await conn.run_sync(Tag.__table__.create)
        await conn.run_sync(ContentItem.__table__.create)
        await conn.run_sync(ContentTag.__table__.create)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(ContentTag.__table__.drop)
        await conn.run_sync(ContentItem.__table__.drop)
        await conn.run_sync(Tag.__table__.drop)
        await conn.run_sync(WorkspaceMember.__table__.drop)
        await conn.run_sync(Workspace.__table__.drop)


@pytest.mark.asyncio
async def test_content_item_crud(db_session: AsyncSession, content_tables, test_user):
    ws = Workspace(id=uuid4(), name="WS", slug="ws", owner_user_id=test_user.id)
    db_session.add(ws)
    db_session.add(
        WorkspaceMember(
            workspace_id=ws.id, user_id=test_user.id, role=WorkspaceRole.owner
        )
    )
    await db_session.commit()

    item = await ContentItemDAO.create(
        db_session,
        workspace_id=ws.id,
        type="article",
        slug="art1",
        title="Article 1",
    )
    await db_session.commit()
    assert item.id is not None

    items = await ContentItemDAO.list_by_type(
        db_session, workspace_id=ws.id, content_type="article"
    )
    assert len(items) == 1 and items[0].id == item.id

    search_items = await ContentItemDAO.search(
        db_session,
        workspace_id=ws.id,
        content_type="article",
        q="Article",
    )
    assert search_items and search_items[0].id == item.id

    tag = Tag(workspace_id=ws.id, slug="t1", name="Tag1")
    db_session.add(tag)
    await db_session.commit()

    ct = await ContentItemDAO.attach_tag(
        db_session, content_id=item.id, tag_id=tag.id, workspace_id=ws.id
    )
    await db_session.commit()
    assert ct.tag_id == tag.id

    await ContentItemDAO.detach_tag(
        db_session, content_id=item.id, tag_id=tag.id
    )
    await db_session.commit()

    res = await db_session.execute(
        select(ContentTag).where(ContentTag.content_id == item.id)
    )
    assert res.first() is None
