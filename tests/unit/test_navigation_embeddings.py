from __future__ import annotations

import math

from domains.product.navigation.application.ports import NodesPort
from domains.product.navigation.application.service import NavigationService, NodeSnapshot
from domains.product.navigation.domain.transition import TransitionContext


class StubNodesPort(NodesPort):
    def __init__(self, nodes: dict[int, dict]):
        self._nodes = nodes

    def list_by_author(self, author_id: str, *, limit: int = 50, offset: int = 0):
        return [node for node in self._nodes.values() if node.get("author_id") == author_id]

    def get(self, node_id: int):
        return self._nodes.get(node_id)

    def search_by_embedding(self, embedding, *, limit: int = 64):
        return list(self._nodes.values())


from datetime import UTC, datetime


def make_context():
    return TransitionContext(
        session_id="s",
        user_id="u",
        origin_node_id=None,
        route_window=tuple(),
        limit_state="normal",
        premium_level="free",
        mode="normal",
        requested_ui_slots=3,
        policies_hash=None,
        cache_seed="seed",
        created_at=datetime.now(tz=UTC),
    )


def test_compose_query_embedding_uses_origin():
    service = NavigationService(nodes=StubNodesPort({}))
    origin = NodeSnapshot(
        id=1, author_id="u", title=None, tags=(), is_public=True, embedding=(1.0, 0.0)
    )
    query = service._compose_query_embedding(origin, [], make_context())
    assert query is not None
    assert math.isclose(query[0], 1.0, rel_tol=1e-6)


def test_embedding_similarity_basic():
    service = NavigationService(nodes=StubNodesPort({}))
    assert math.isclose(service._embedding_similarity((1.0, 0.0), (1.0, 0.0)), 1.0)
    assert service._embedding_similarity((1.0, 0.0), (0.0, 1.0)) == 0.0
