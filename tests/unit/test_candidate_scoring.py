from __future__ import annotations

import asyncio
from dataclasses import dataclass
from types import SimpleNamespace

from apps.backend.app.core.preview import PreviewContext
from apps.backend.app.domains.navigation.application.policies import ManualPolicy
from apps.backend.app.domains.navigation.application.providers import TransitionProvider
from apps.backend.app.domains.navigation.application.router import TransitionRouter


@dataclass
class DummyNode:
    slug: str
    tags: list[str] | None = None
    premium_only: bool = False
    workspace_id: str = "ws"
    is_visible: bool = True
    is_public: bool = True
    is_recommendable: bool = True
    nft_required: str | None = None


class StaticProvider(TransitionProvider):
    def __init__(self, mapping):
        self.mapping = mapping

    async def get_transitions(self, db, node, user, workspace_id):
        return self.mapping.get(node.slug, [])


def _run(router, start):
    budget = SimpleNamespace(
        max_time_ms=1000, max_queries=1000, max_filters=1000, fallback_chain=[]
    )
    return asyncio.run(router.route(None, start, None, budget, preview=PreviewContext()))


def test_weight_repeat_and_novelty():
    start = DummyNode("start", tags=["t1"])
    repeat = DummyNode("repeat", tags=["t1"])
    repeat.weight = 10
    new = DummyNode("new", tags=["t2"])
    new.weight = 5
    provider = StaticProvider({"start": [repeat, new]})
    router = TransitionRouter(
        [ManualPolicy(provider)],
        not_repeat_last=0,
        no_repeat_window=5,
        repeat_threshold=0,
        repeat_decay=0.5,
    )
    result = _run(router, start)
    assert result.next.slug == "new"
    trace = router.trace[0]
    assert trace.scores["new"] > trace.scores["repeat"]


def test_premium_filtered():
    start = DummyNode("start")
    premium = DummyNode("p", premium_only=True)
    normal = DummyNode("n")
    provider = StaticProvider({"start": [premium, normal]})
    router = TransitionRouter([ManualPolicy(provider)], not_repeat_last=0)
    result = _run(router, start)
    assert result.next.slug == "n"
    trace = router.trace[0]
    assert "p" not in trace.scores
