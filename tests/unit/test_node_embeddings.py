from __future__ import annotations

import pytest

from domains.product.nodes.adapters.repo_memory import MemoryNodesRepo
from domains.product.nodes.adapters.tag_catalog_memory import MemoryTagCatalog
from domains.product.nodes.application.service import NodeService


class StubEmbeddingClient:
    def __init__(self, vector: list[float]):
        self.vector = vector
        self.enabled = True
        self.calls: list[str] = []

    async def embed(self, text: str) -> list[float]:
        self.calls.append(text)
        return list(self.vector)


def make_service(vector: list[float] | None = None) -> NodeService:
    repo = MemoryNodesRepo()
    tags = MemoryTagCatalog()

    class Outbox:
        def __init__(self) -> None:
            self.events: list[tuple[str, dict]] = []

        def publish(self, topic: str, payload: dict, key: str | None = None) -> None:
            self.events.append((topic, payload))

    outbox = Outbox()
    embedding = StubEmbeddingClient(vector or [0.1, 0.2, 0.3]) if vector is not None else None
    service = NodeService(repo=repo, tags=tags, outbox=outbox, usage=None, embedding=embedding)
    service._repo = repo  # type: ignore[attr-defined]
    service._embedding_stub = embedding  # type: ignore[attr-defined]
    service._outbox_stub = outbox  # type: ignore[attr-defined]
    return service


@pytest.mark.asyncio
async def test_create_enqueues_embedding_and_worker_updates() -> None:
    service = make_service([0.9, 0.1])
    view = await service.create(
        author_id="00000000-0000-0000-0000-000000000001",
        title="My Node",
        tags=["Alpha"],
        is_public=True,
        status="published",
        content_html="<p>Some content</p>",
    )
    assert view.embedding is None
    events = service._outbox_stub.events  # type: ignore[attr-defined]
    assert any(topic == "node.embedding.requested.v1" for topic, _ in events)
    refreshed = await service.recompute_embedding(view.id, reason="worker")
    assert refreshed is not None
    assert refreshed.embedding == [0.9, 0.1]


@pytest.mark.asyncio
async def test_update_tags_schedules_recompute() -> None:
    service = make_service([0.5, 0.5])
    view = await service.create(
        author_id="00000000-0000-0000-0000-000000000002",
        title="Node",
        tags=["beta"],
        is_public=True,
        status="published",
        content_html="<p>First</p>",
    )
    # simulate worker running once so node has baseline embedding
    await service.recompute_embedding(view.id, reason="bootstrap")
    service._outbox_stub.events.clear()  # type: ignore[attr-defined]

    await service.update_tags(view.id, ["gamma"], actor_id="actor")
    events = service._outbox_stub.events  # type: ignore[attr-defined]
    assert events and events[-1][0] == "node.embedding.requested.v1"

    refreshed = await service.recompute_embedding(view.id, reason="worker")
    assert refreshed is not None
    assert refreshed.embedding == [0.5, 0.5]


@pytest.mark.asyncio
async def test_update_title_schedules_recompute() -> None:
    service = make_service([0.2, 0.8])
    view = await service.create(
        author_id="00000000-0000-0000-0000-000000000003",
        title="Original",
        tags=["delta"],
        is_public=True,
        status="published",
        content_html="body",
    )
    await service.recompute_embedding(view.id, reason="bootstrap")
    service._outbox_stub.events.clear()  # type: ignore[attr-defined]

    await service.update(view.id, title="Updated")
    events = service._outbox_stub.events  # type: ignore[attr-defined]
    assert events and events[-1][0] == "node.embedding.requested.v1"

    refreshed = await service.recompute_embedding(view.id, reason="worker")
    assert refreshed is not None
    assert refreshed.embedding == [0.2, 0.8]
