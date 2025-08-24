from pathlib import Path
import asyncio
import importlib
import sys
from dataclasses import dataclass
from types import SimpleNamespace
from typing import List, Optional

import pytest

# Ensure apps package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.modules.setdefault("app", importlib.import_module("apps.backend.app"))

from apps.backend.app.domains.navigation.application.transition_router import (
    ManualPolicy,
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


def make_router():
    start = DummyNode("start")
    manual_provider = StaticProvider({"start": [DummyNode("manual1")]})
    random_provider = RandomListProvider({"manual1": [DummyNode("r1"), DummyNode("r2")]})
    policies = [
        ManualPolicy(manual_provider),
        RandomPolicy(random_provider),
    ]
    return TransitionRouter(policies, not_repeat_last=5), start


async def _build_route(router, start, steps, seed=None):
    budget = SimpleNamespace(time_ms=1000, db_queries=1000, fallback_chain=[])
    route = [start]
    current = start
    for _ in range(steps):
        result = await router.route(None, current, None, budget, seed=seed)
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
