import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.application.node_query_service import NodeQueryService
from app.domains.nodes.application.query_models import NodeFilterSpec, PageRequest, QueryContext
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.tags.infrastructure.models.tag_models import Tag, NodeTag


@pytest.mark.asyncio
async def test_query_filters_and_etag(db_session: AsyncSession, test_user):
    # Arrange: create nodes and tags
    n1 = Node(title="Alpha", content={"text": "alpha nodes"}, author_id=test_user.id, is_public=True, is_visible=True)
    n2 = Node(title="Beta", content={"text": "beta nodes"}, author_id=test_user.id, is_public=False, is_visible=True)
    n3 = Node(title="Gamma", content={"text": "beta gamma"}, author_id=test_user.id, is_public=True, is_visible=False)
    n1.views, n2.views = 5, 20
    n1.reactions, n2.reactions = 1, 7
    tag_a = Tag(slug="a", name="a")
    tag_b = Tag(slug="b", name="b")
    db_session.add_all([n1, n2, n3, tag_a, tag_b])
    await db_session.flush()
    db_session.add_all([
        NodeTag(node_id=n1.id, tag_id=tag_a.id),
        NodeTag(node_id=n1.id, tag_id=tag_b.id),
        NodeTag(node_id=n2.id, tag_id=tag_a.id),
    ])
    await db_session.commit()

    svc = NodeQueryService(db_session)
    page = PageRequest(offset=0, limit=50)
    ctx = QueryContext(user=None, is_admin=False)

    # any mode (a): n1 and n2
    spec_any = NodeFilterSpec(tags=["a"], match="any")
    items_any = await svc.list_nodes(spec_any, page, ctx)
    slugs_any = {x.slug for x in items_any}
    assert slugs_any.issuperset({n1.slug, n2.slug})

    # all mode (a+b): only n1
    spec_all = NodeFilterSpec(tags=["a", "b"], match="all")
    items_all = await svc.list_nodes(spec_all, page, ctx)
    assert any(x.id == n1.id for x in items_all)
    assert all(x.id != n2.id for x in items_all)

    # author filter + q (beta)
    spec_author_q = NodeFilterSpec(author_id=test_user.id, q="beta")
    items_author_q = await svc.list_nodes(spec_author_q, page, ctx)
    slugs_q = {x.slug for x in items_author_q}
    assert n2.slug in slugs_q or n3.slug in slugs_q

    # min_views + sort by views_desc
    spec_views = NodeFilterSpec(min_views=10, sort="views_desc")
    items_views = await svc.list_nodes(spec_views, page, ctx)
    assert items_views and items_views[0].views >= 10

    # min_reactions + sort by reactions_desc
    spec_react = NodeFilterSpec(min_reactions=2, sort="reactions_desc")
    items_react = await svc.list_nodes(spec_react, page, ctx)
    assert items_react and (getattr(items_react[0], "reactions", 0) >= 2)

    # ETag should change after update
    etag_before = await svc.compute_nodes_etag(NodeFilterSpec(), ctx, page)
    n1.title = "Alpha v2"
    await db_session.flush()
    n1.updated_at = datetime.utcnow()
    await db_session.commit()
    etag_after = await svc.compute_nodes_etag(NodeFilterSpec(), ctx, page)
    assert etag_before != etag_after
