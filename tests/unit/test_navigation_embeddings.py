from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from domains.product.navigation.application.ports import NodesPort, TransitionRequest
from domains.product.navigation.application.service import (
    NavigationService,
    NodeSnapshot,
    _CandidateEnvelope,
)
from domains.product.navigation.config import ModeConfig
from domains.product.navigation.domain.transition import (
    TransitionCandidate,
    TransitionContext,
)


class StubNodesPort(NodesPort):
    def __init__(self, nodes: dict[int, dict]):
        self._nodes = nodes

    def list_by_author(self, author_id: str, *, limit: int = 50, offset: int = 0):
        return [
            node for node in self._nodes.values() if node.get("author_id") == author_id
        ][:limit]

    def get(self, node_id: int):
        return self._nodes.get(node_id)

    def search_by_embedding(self, embedding, *, limit: int = 64):
        return list(self._nodes.values())


@dataclass
class RichNodesPort(NodesPort):
    nodes: dict[int, dict]
    embedding_results: list[dict]

    def list_by_author(self, author_id: str, *, limit: int = 50, offset: int = 0):
        return [
            node for node in self.nodes.values() if node.get("author_id") == author_id
        ][:limit]

    def get(self, node_id: int):
        return self.nodes.get(node_id)

    def search_by_embedding(self, embedding, *, limit: int = 64):
        return self.embedding_results[:limit]


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


def make_snapshot(
    node_id: int, tags: tuple[str, ...] = (), *, author: str = "author"
) -> NodeSnapshot:
    return NodeSnapshot(
        id=node_id,
        author_id=author,
        title=f"Node {node_id}",
        tags=tags,
        is_public=True,
        embedding=(1.0, 0.0),
    )


def test_compose_query_embedding_uses_origin():
    service = NavigationService(nodes=StubNodesPort({}))
    origin = make_snapshot(1)
    query = service._compose_query_embedding(origin, [], make_context())
    assert query is not None
    assert math.isclose(query[0], 1.0, rel_tol=1e-6)


def test_embedding_similarity_basic():
    service = NavigationService(nodes=StubNodesPort({}))
    assert math.isclose(service._embedding_similarity((1.0, 0.0), (1.0, 0.0)), 1.0)
    assert service._embedding_similarity((1.0, 0.0), (0.0, 1.0)) == 0.0


def test_score_snapshot_compass_uses_similarity_and_overlap():
    service = NavigationService(nodes=StubNodesPort({}))
    origin = make_snapshot(1, tags=("python", "ai"))
    snapshot = NodeSnapshot(
        id=2,
        author_id="other",
        title="Other",
        tags=("Python", "ml"),
        is_public=True,
        embedding=(0.9, 0.1),
    )

    score, factors = service._score_snapshot(
        snapshot,
        provider="compass",
        origin=origin,
        query_embedding=(0.8, 0.2),
    )

    assert score > 0
    assert "similarity" in factors
    assert "tag_overlap" in factors


def test_score_snapshot_echo_accounts_for_author_match():
    service = NavigationService(nodes=StubNodesPort({}), base_weights={"echo": 0.5})
    origin = make_snapshot(1, tags=("python", "ai"))
    snapshot = make_snapshot(2, tags=("Python", "sql"))

    score, factors = service._score_snapshot(
        snapshot,
        provider="echo",
        origin=origin,
        query_embedding=None,
    )

    assert score > 0.5
    assert factors["author_match"] == 1.0
    assert factors["tag_overlap"] > 0


def test_score_snapshot_random_uses_baseline():
    service = NavigationService(nodes=StubNodesPort({}), base_weights={"fresh": 0.5})
    snapshot = make_snapshot(3)

    score, factors = service._score_snapshot(
        snapshot,
        provider="random",
        origin=None,
        query_embedding=None,
    )

    assert score == pytest.approx(0.5)
    assert factors["baseline"] == pytest.approx(0.5)


def test_tag_overlap_handles_case_insensitive_tags():
    service = NavigationService(nodes=StubNodesPort({}))
    left = make_snapshot(1, tags=("Python", "FastAPI"))
    right = make_snapshot(2, tags=("python", "sqlalchemy"))

    overlap = service._tag_overlap(left, right)

    assert overlap == pytest.approx(0.5)


def test_finalize_candidates_computes_probabilities():
    service = NavigationService(nodes=StubNodesPort({}))
    envelopes = [
        _CandidateEnvelope(
            snapshot=make_snapshot(1),
            provider="compass",
            score=0.8,
            factors={"similarity": 0.9},
        ),
        _CandidateEnvelope(
            snapshot=make_snapshot(2),
            provider="random",
            score=0.2,
            factors={},
        ),
    ]

    candidates = service._finalize_candidates(envelopes, limit=2)

    assert len(candidates) == 2
    assert candidates[0].node_id == 1
    assert math.isclose(sum(c.probability for c in candidates), 1.0)
    assert candidates[0].badge in {"trail", "similar", "explore"}


def test_build_telemetry_counts_providers():
    service = NavigationService(nodes=StubNodesPort({}))
    candidates = [
        TransitionCandidate(
            node_id=1,
            provider="compass",
            score=1.0,
            probability=0.6,
            factors={},
            badge="similar",
            explain="",
        ),
        TransitionCandidate(
            node_id=2,
            provider="random",
            score=0.5,
            probability=0.4,
            factors={},
            badge="explore",
            explain="",
        ),
    ]

    telemetry = service._build_telemetry(candidates, query_embedding=(0.1, 0.9))

    assert telemetry["candidates_total"] == 2.0
    assert telemetry["query_embedding"] == 1.0
    assert telemetry["provider_compass_count"] == 1.0
    assert telemetry["provider_random_count"] == 1.0


def test_navigation_service_pipeline_produces_decision():
    nodes = {
        1: {
            "id": 1,
            "author_id": "author",
            "title": "Origin",
            "tags": ["Python", "AI"],
            "is_public": True,
            "embedding": [1.0, 0.0],
        },
        2: {
            "id": 2,
            "author_id": "author",
            "title": "Echo",
            "tags": ["Python", "Data"],
            "is_public": True,
            "embedding": [0.9, 0.1],
        },
        3: {
            "id": 3,
            "author_id": "other",
            "title": "Compass-1",
            "tags": ["AI"],
            "is_public": True,
            "embedding": [0.8, 0.2],
        },
        4: {
            "id": 4,
            "author_id": "other",
            "title": "Compass-2",
            "tags": ["Python"],
            "is_public": True,
            "embedding": [0.7, 0.3],
        },
        5: {
            "id": 5,
            "author_id": "author",
            "title": "Echo-2",
            "tags": ["Rust"],
            "is_public": True,
            "embedding": [0.2, 0.8],
        },
        6: {
            "id": 6,
            "author_id": "author",
            "title": "Random-1",
            "tags": ["Go"],
            "is_public": True,
            "embedding": [0.3, 0.7],
        },
        7: {
            "id": 7,
            "author_id": "friend",
            "title": "History",
            "tags": ["History"],
            "is_public": True,
            "embedding": [0.5, 0.5],
        },
    }
    port = RichNodesPort(nodes=nodes, embedding_results=[nodes[3], nodes[4]])
    custom_mode = ModeConfig(
        name="custom",
        providers=("compass", "random", "echo"),
        k_base=3,
        temperature=0.2,
        epsilon=0.1,
        author_threshold=1,
        tag_threshold=1,
        allow_random=True,
    )
    service = NavigationService(
        nodes=port,
        mode_configs={"custom": custom_mode},
        base_weights={
            "tag_sim": 0.6,
            "diversity_bonus": 0.3,
            "echo": 1.0,
            "fresh": 0.2,
        },
        badges={"random": "explore"},
    )
    service._random.random = lambda: 0.42
    service._random.shuffle = lambda seq: None

    request = TransitionRequest(
        user_id="author",
        session_id="sess-1",
        origin_node_id=1,
        route_window=(7, "7", "bad", 2, 2),
        limit_state="normal",
        mode="custom",
        requested_ui_slots=2,
        premium_level="gold",
        policies_hash="abc",
        requested_provider_overrides=[" compass ", "ECHO", "random"],
        emergency=False,
    )

    decision = service.next(request)

    assert decision.mode == "custom"
    assert decision.selected_node_id in {3, 4, 5, 6}
    assert decision.empty_pool is False
    providers = {candidate.provider for candidate in decision.candidates}
    assert "compass" in providers
    assert "random" in providers
    assert decision.telemetry["candidates_total"] == float(len(decision.candidates))
    assert service._mode_configs["custom"] is custom_mode
