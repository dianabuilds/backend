import asyncio
import importlib
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import List, Optional

from hypothesis import given
from hypothesis import strategies as st

# Ensure apps package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.modules.setdefault("app", importlib.import_module("apps.backend.app"))

from apps.backend.app.core.preview import PreviewContext
from apps.backend.app.domains.navigation.application.transition_router import (
    CompassPolicy,
    ManualPolicy,
    NoRouteReason,
    RandomPolicy,
    TransitionProvider,
    TransitionRouter,
)


@dataclass
class DummyNode:
    slug: str
    workspace_id: str = "ws"
    tags: Optional[List[str]] = None
    source: Optional[str] = None


class StaticProvider(TransitionProvider):
    def __init__(self, mapping):
        self.mapping = mapping

    async def get_transitions(self, db, node, user, workspace_id):
        return self.mapping.get(node.slug, [])


class RandomListProvider(TransitionProvider):
    def __init__(self, mapping):
        self.mapping = mapping

    async def get_transitions(self, db, node, user, workspace_id):
        return self.mapping.get(node.slug, [])


class WorkspaceProvider(TransitionProvider):
    """Return only nodes that belong to provided workspace."""

    def __init__(self, mapping):
        self.mapping = mapping

    async def get_transitions(self, db, node, user, workspace_id):
        candidates = self.mapping.get(node.slug, [])
        return [n for n in candidates if n.workspace_id == workspace_id]


def make_router():
    start = DummyNode("start")
    manual_provider = StaticProvider({"start": [DummyNode("manual1")]})
    random_provider = RandomListProvider(
        {"manual1": [DummyNode("r1"), DummyNode("r2")]}
    )
    policies = [
        ManualPolicy(manual_provider),
        RandomPolicy(random_provider),
    ]
    return TransitionRouter(policies, not_repeat_last=5), start


class ConditionalPolicy(ManualPolicy):
    name = "conditional"


async def _build_route(router, start, steps, seed=None):
    budget = SimpleNamespace(
        max_time_ms=1000, max_queries=1000, max_filters=1000, fallback_chain=[]
    )
    route = [start]
    current = start
    for _ in range(steps):
        result = await router.route(
            None, current, None, budget, seed=seed, preview=PreviewContext()
        )
        if result.next is None:
            break
        current = result.next
        route.append(current)
    return route


def test_route_reproducible():
    router1, start1 = make_router()
    router2, start2 = make_router()
    route1 = asyncio.run(_build_route(router1, start1, 2, seed=42))
    route2 = asyncio.run(_build_route(router2, start2, 2, seed=42))
    assert [n.slug for n in route1] == [n.slug for n in route2]


def test_no_loops():
    loop_provider = StaticProvider({"a": [DummyNode("b")], "b": [DummyNode("a")]})
    router = TransitionRouter([ManualPolicy(loop_provider)], not_repeat_last=10)
    start = DummyNode("a")
    route = asyncio.run(_build_route(router, start, 5))
    slugs = [n.slug for n in route]
    assert len(slugs) == len(set(slugs))


def test_local_resonance_stops():
    provider = StaticProvider(
        {
            "a": [DummyNode("b", tags=["t"])],
            "b": [DummyNode("a", tags=["t"])],
        }
    )
    router = TransitionRouter(
        [ManualPolicy(provider)],
        not_repeat_last=0,
        no_repeat_window=5,
        repeat_threshold=0.3,
        repeat_decay=0.5,
        max_visits=10,
    )
    start = DummyNode("a", tags=["t"])
    route = asyncio.run(_build_route(router, start, 5))
    assert [n.slug for n in route] == ["a", "b"]


def test_threshold_respected():
    provider = StaticProvider({"a": [DummyNode("b", tags=["t"])]})
    router = TransitionRouter(
        [ManualPolicy(provider)],
        not_repeat_last=0,
        no_repeat_window=5,
        repeat_threshold=0.6,
        repeat_decay=0.5,
        max_visits=10,
    )
    start = DummyNode("a", tags=["t"])
    route = asyncio.run(_build_route(router, start, 5))
    # Second node filtered immediately due to high threshold
    assert [n.slug for n in route] == ["a"]


def test_no_route_on_empty_graph():
    provider = StaticProvider({})
    router = TransitionRouter([ManualPolicy(provider)], not_repeat_last=0)
    start = DummyNode("start")
    budget = SimpleNamespace(
        max_time_ms=1000, max_queries=1000, max_filters=1000, fallback_chain=[]
    )
    result = asyncio.run(
        router.route(None, start, None, budget, preview=PreviewContext())
    )
    assert result.next is None
    assert result.reason == NoRouteReason.NO_ROUTE


def test_hidden_archived_filtered():
    start = DummyNode("start")
    hidden = DummyNode("hidden")
    archived = DummyNode("archived")
    visible = DummyNode("visible")
    provider = StaticProvider({"start": [hidden, archived, visible]})
    router = TransitionRouter([ManualPolicy(provider)], not_repeat_last=5)
    router.history.extend(["hidden", "archived"])
    route = asyncio.run(_build_route(router, start, 1))
    assert [n.slug for n in route] == ["start", "visible"]


def test_policy_priority():
    start = DummyNode("start")
    provider1 = StaticProvider({"start": [DummyNode("p1")]})
    provider2 = StaticProvider({"start": [DummyNode("p2")]})
    router = TransitionRouter(
        [ManualPolicy(provider1), ManualPolicy(provider2)], not_repeat_last=0
    )
    route = asyncio.run(_build_route(router, start, 1))
    assert [n.slug for n in route] == ["start", "p1"]


def test_fallback_chain_sequence():
    start = DummyNode("start")
    manual_provider = StaticProvider({"start": []})
    conditional_provider = StaticProvider({"start": []})
    compass_provider = StaticProvider({"start": [DummyNode("c1")]})
    policies = [
        ManualPolicy(manual_provider),
        ConditionalPolicy(conditional_provider),
        CompassPolicy(compass_provider),
    ]
    router = TransitionRouter(policies, not_repeat_last=5)
    budget = SimpleNamespace(
        max_time_ms=1000,
        max_queries=1000,
        max_filters=1000,
        fallback_chain=["manual", "conditional", "compass"],
    )
    result = asyncio.run(
        router.route(None, start, None, budget, preview=PreviewContext())
    )
    assert result.next and result.next.slug == "c1"
    assert result.metrics.get("fallback_used")


def test_workspace_isolation():
    start = DummyNode("start", workspace_id="ws1")
    provider = WorkspaceProvider(
        {
            "start": [
                DummyNode("a", workspace_id="ws1"),
                DummyNode("b", workspace_id="ws2"),
            ]
        }
    )
    router = TransitionRouter([ManualPolicy(provider)], not_repeat_last=0)
    route = asyncio.run(_build_route(router, start, 1))
    assert [n.slug for n in route] == ["start", "a"]


@given(st.integers(min_value=0, max_value=1000))
def test_determinism_property(seed):
    router1, start1 = make_router()
    router2, start2 = make_router()
    r1 = asyncio.run(_build_route(router1, start1, 2, seed))
    r2 = asyncio.run(_build_route(router2, start2, 2, seed))
    assert [n.slug for n in r1] == [n.slug for n in r2]


@given(st.integers(min_value=1, max_value=5))
def test_no_repeat_window_property(window):
    provider = StaticProvider({"a": [DummyNode("a", tags=["t"])]})
    router = TransitionRouter(
        [ManualPolicy(provider)],
        not_repeat_last=0,
        no_repeat_window=window,
        repeat_threshold=0.6,
        repeat_decay=0.5,
        max_visits=10,
    )
    start = DummyNode("a", tags=["t"])
    route = asyncio.run(_build_route(router, start, window * 2))
    assert len(route) <= window + 1


@given(st.floats(min_value=0.1, max_value=0.9), st.floats(min_value=0.1, max_value=0.9))
def test_diversity_weight_monotonic(decay1, decay2):
    if decay1 > decay2:
        decay1, decay2 = decay2, decay1
    provider = StaticProvider(
        {"a": [DummyNode("a", tags=["t"]), DummyNode("a", tags=["t"])]}
    )
    start = DummyNode("a", tags=["t"])
    router1 = TransitionRouter(
        [ManualPolicy(provider)],
        not_repeat_last=0,
        no_repeat_window=5,
        repeat_threshold=0.4,
        repeat_decay=decay1,
        max_visits=10,
    )
    router2 = TransitionRouter(
        [ManualPolicy(provider)],
        not_repeat_last=0,
        no_repeat_window=5,
        repeat_threshold=0.4,
        repeat_decay=decay2,
        max_visits=10,
    )
    r1 = asyncio.run(_build_route(router1, start, 5))
    r2 = asyncio.run(_build_route(router2, start, 5))
    assert len(r1) <= len(r2)
