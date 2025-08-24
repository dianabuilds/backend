import importlib
import sys
from dataclasses import dataclass
from pathlib import Path

import asyncio
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


def make_router(seed: int):
    start = DummyNode("start")
    manual_provider = StaticProvider({"start": [DummyNode("manual1")]})
    random_provider = RandomListProvider({"manual1": [DummyNode("r1"), DummyNode("r2")]})
    policies = [
        ManualPolicy(manual_provider),
        RandomPolicy(random_provider, seed=seed),
    ]
    return TransitionRouter(policies, not_repeat_last=5), start


def test_route_reproducible():
    router1, start = make_router(seed=42)
    route1 = asyncio.run(router1.route(None, start, None, 2))
    router2, start2 = make_router(seed=42)
    route2 = asyncio.run(router2.route(None, start2, None, 2))
    assert [n.slug for n in route1] == [n.slug for n in route2]


def test_no_loops():
    loop_provider = StaticProvider({"a": [DummyNode("b")], "b": [DummyNode("a")]})
    router = TransitionRouter([ManualPolicy(loop_provider)], not_repeat_last=10)
    start = DummyNode("a")
    route = asyncio.run(router.route(None, start, None, 5))
    slugs = [n.slug for n in route]
    assert len(slugs) == len(set(slugs))
