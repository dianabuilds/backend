import pytest
import pytest
import pytest_asyncio
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.workspaces.infrastructure.models import Workspace
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.infrastructure.repositories.node_repository import NodeRepositoryAdapter
from app.domains.nodes.application.node_query_service import NodeQueryService
from app.domains.nodes.application.query_models import NodeFilterSpec, PageRequest, QueryContext
from app.schemas.node import NodeCreate
from app.domains.content.models import ContentItem  # noqa: F401
from app.domains.tags.models import Tag  # noqa: F401
from app.domains.tags.infrastructure.models.tag_models import NodeTag


@pytest_asyncio.fixture()
async def node_tables(db_session: AsyncSession):
    await db_session.run_sync(lambda s: Workspace.__table__.create(s.bind, checkfirst=True))
    await db_session.run_sync(lambda s: Tag.__table__.create(s.bind, checkfirst=True))
    await db_session.run_sync(lambda s: Node.__table__.create(s.bind, checkfirst=True))
    await db_session.run_sync(lambda s: NodeTag.__table__.create(s.bind, checkfirst=True))
    yield
    await db_session.run_sync(lambda s: NodeTag.__table__.drop(s.bind, checkfirst=True))
    await db_session.run_sync(lambda s: Node.__table__.drop(s.bind, checkfirst=True))
    await db_session.run_sync(lambda s: Tag.__table__.drop(s.bind, checkfirst=True))
    await db_session.run_sync(lambda s: Workspace.__table__.drop(s.bind, checkfirst=True))


@pytest.mark.asyncio
async def test_repository_scopes_by_workspace(db_session: AsyncSession, test_user, node_tables):
    ws1 = Workspace(id=uuid4(), name="WS1", slug="ws1", owner_user_id=test_user.id)
    ws2 = Workspace(id=uuid4(), name="WS2", slug="ws2", owner_user_id=test_user.id)
    db_session.add_all([ws1, ws2])
    await db_session.commit()
    repo = NodeRepositoryAdapter(db_session)
    payload = NodeCreate(title="A", content={})
    n1 = await repo.create(payload, test_user.id, ws1.id)
    n2 = await repo.create(payload, test_user.id, ws2.id)

    assert await repo.get_by_slug(n1.slug, ws1.id)
    assert await repo.get_by_slug(n1.slug, ws2.id) is None
    assert await repo.get_by_id(n2.id, ws2.id)
    assert await repo.get_by_id(n2.id, ws1.id) is None


@pytest.mark.asyncio
async def test_query_service_scopes_by_workspace(db_session: AsyncSession, test_user, node_tables):
    ws1 = Workspace(id=uuid4(), name="WS1", slug="ws1", owner_user_id=test_user.id)
    ws2 = Workspace(id=uuid4(), name="WS2", slug="ws2", owner_user_id=test_user.id)
    db_session.add_all([ws1, ws2])
    await db_session.commit()
    repo = NodeRepositoryAdapter(db_session)
    payload = NodeCreate(title="A", content={})
    n1 = await repo.create(payload, test_user.id, ws1.id)
    await repo.create(payload, test_user.id, ws2.id)

    svc = NodeQueryService(db_session)
    spec = NodeFilterSpec(workspace_id=ws1.id)
    ctx = QueryContext(user=test_user, is_admin=True)
    page = PageRequest(limit=10, offset=0)
    nodes = await svc.list_nodes(spec, page, ctx)
    assert {n.id for n in nodes} == {n1.id}
