import asyncio
import importlib
import sys
import uuid
from dataclasses import dataclass
from types import SimpleNamespace

# Ensure apps package is importable
app_module = importlib.import_module("apps.backend.app")
sys.modules.setdefault("app", app_module)

from app.core.preview import PreviewContext  # noqa: E402
from app.domains.navigation.application.transition_router import (  # noqa: E402
    RandomPolicy,
    TransitionProvider,
    TransitionRouter,
)


@dataclass
class DummyNode:
    slug: str
    workspace_id: uuid.UUID = uuid.uuid4()


class DictProvider(TransitionProvider):
    def __init__(self, mapping):
        self.mapping = mapping

    async def get_transitions(self, db, node, user, workspace_id, preview=None):
        return [DummyNode(s) for s in self.mapping.get(node.slug, [])]


def test_dry_run_deterministic():
    async def _run():
        provider = DictProvider({"start": ["a", "b", "c", "d"]})
        policy = RandomPolicy(provider)
        router = TransitionRouter([policy])
        start = DummyNode("start")
        budget = SimpleNamespace(
            max_time_ms=1000, max_queries=1000, max_filters=1000, fallback_chain=[]
        )

        preview = PreviewContext(mode="dry_run", seed=1)
        res1 = await router.route(None, start, None, budget, preview=preview)
        res2 = await router.route(None, start, None, budget, preview=preview)
        res3 = await router.route(
            None, start, None, budget, preview=PreviewContext(mode="dry_run", seed=2)
        )

        assert res1.trace == res2.trace
        assert res1.trace != res3.trace
        assert list(router.history) == []

    asyncio.run(_run())
