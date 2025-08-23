import types
from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.domains.nodes.application.node_query_service import NodeQueryService
from app.domains.nodes.application.query_models import (
    NodeFilterSpec,
    PageRequest,
    QueryContext,
)


class FakeResult:
    def __init__(self, first_tuple):
        self._first = first_tuple

    def first(self):
        return self._first


class FakeDB:
    def __init__(self, first_tuple):
        self._first_tuple = first_tuple

    async def execute(self, stmt):
        return FakeResult(self._first_tuple)


@pytest.mark.asyncio
async def test_compute_nodes_etag_basic():
    now = datetime.utcnow()
    db = FakeDB((123, now))
    svc = NodeQueryService(db)  # type: ignore
    spec = NodeFilterSpec(tags=["a", "b"], match="all", q="alpha", min_views=10)
    page = PageRequest(offset=0, limit=20)
    ctx = QueryContext(user=types.SimpleNamespace(id=str(uuid4())), is_admin=False)
    etag = await svc.compute_nodes_etag(spec, ctx, page)
    assert isinstance(etag, str)
    assert len(etag) == 64


@pytest.mark.asyncio
async def test_compute_nodes_etag_with_author_and_dates():
    now = datetime.utcnow()
    db = FakeDB((10, now - timedelta(days=1)))
    svc = NodeQueryService(db)  # type: ignore
    spec = NodeFilterSpec(
        tags=None,
        match="any",
        author_id=uuid4(),
        is_public=True,
        is_visible=True,
        created_from=now - timedelta(days=7),
        created_to=now,
        updated_from=now - timedelta(days=3),
        updated_to=now,
        sort="created_desc",
        q="beta",
        min_reactions=5,
    )
    page = PageRequest(offset=10, limit=10)
    ctx = QueryContext(user=None, is_admin=False)
    etag = await svc.compute_nodes_etag(spec, ctx, page)
    assert isinstance(etag, str)
    assert len(etag) == 64
