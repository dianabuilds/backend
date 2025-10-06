import pytest
from types import SimpleNamespace

from domains.platform.events.adapters.outbox_memory import InMemoryOutbox
from domains.product.nodes.adapters.memory.repository import MemoryNodesRepo
from domains.product.nodes.adapters.memory.tag_catalog import MemoryTagCatalog
from domains.product.nodes.adapters.sql.repository import (
    create_repo as create_nodes_repo,
)
from domains.product.nodes.application.service import NodeService


@pytest.mark.asyncio
async def test_nodes_service_uses_memory_fallback_when_sql_unavailable():
    memory_repo = MemoryNodesRepo()
    settings = SimpleNamespace(database_url=None)

    repo = create_nodes_repo(settings, memory_repo=memory_repo)
    assert repo is memory_repo

    created = await repo.create(
        author_id="user-1",
        title="demo",
        is_public=True,
        tags=["demo"],
        content_html=None,
    )

    service = NodeService(
        repo=repo,
        tags=MemoryTagCatalog(),
        outbox=InMemoryOutbox(),
    )

    fetched = service.get(created.id)
    assert fetched is not None
    assert fetched.title == "demo"
