from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from domains.product.navigation.domain.transition import (
    TransitionCandidate,
    TransitionContext,
    TransitionDecision,
)
from domains.product.site.application import block_preview as bp


class FakeNavigationService:
    def __init__(self, candidates: list[TransitionCandidate]) -> None:
        self._candidates = candidates

    def next(self, request) -> TransitionDecision:  # type: ignore[override]
        context = TransitionContext(
            session_id=request.session_id,
            user_id=request.user_id,
            origin_node_id=request.origin_node_id,
            route_window=tuple(request.route_window),
            limit_state=request.limit_state,
            premium_level=request.premium_level,
            mode=request.mode,
            requested_ui_slots=request.requested_ui_slots,
            policies_hash=request.policies_hash,
            cache_seed="preview-cache-seed",
            created_at=datetime.now(UTC),
        )
        return TransitionDecision(
            context=context,
            candidates=tuple(self._candidates),
            selected_node_id=self._candidates[0].node_id if self._candidates else None,
            ui_slots_granted=len(self._candidates),
            limit_state=request.limit_state,
            mode=request.mode,
            pool_size=len(self._candidates),
            temperature=0.0,
            epsilon=0.0,
            empty_pool=not self._candidates,
        )


class FakeNodesService:
    def __init__(self, nodes: dict[int, dict[str, object]]) -> None:
        self._nodes = {node_id: SimpleNamespace(**payload) for node_id, payload in nodes.items()}

    async def _repo_get_async(self, node_id: int):  # type: ignore[override]
        await asyncio.sleep(0)
        return self._nodes.get(node_id)


@pytest.mark.asyncio()
async def test_recommendations_preview(monkeypatch: pytest.MonkeyPatch) -> None:
    candidate = TransitionCandidate(
        node_id=42,
        provider="compass",
        score=0.9,
        probability=0.8,
        factors={"similarity": 0.9},
        badge="Compass",
        explain="similarity 0.90",
    )
    container = SimpleNamespace(
        navigation_service=FakeNavigationService([candidate]),
        nodes_service=FakeNodesService({42: {"slug": "demo-node", "title": "Demo"}}),
    )

    async def fake_list_nodes_admin(*args, **kwargs):
        return []

    monkeypatch.setattr(bp, "list_nodes_admin", fake_list_nodes_admin)

    preview = await bp.get_block_preview(
        container,
        "recommendations",
        locale="ru",
        limit=3,
    )
    assert preview["source"] == "live"
    assert preview["items"][0]["title"] == "Demo"
    assert preview["items"][0]["href"] == "/n/demo-node"


@pytest.mark.asyncio()
async def test_nodes_preview_falls_back_to_list(monkeypatch: pytest.MonkeyPatch) -> None:
    container = SimpleNamespace(
        navigation_service=None,
        nodes_service=None,
    )

    async def fake_list_nodes_admin(*args, **kwargs):
        return [
            {"id": 1, "slug": "item-1", "title": "Item 1", "author_name": "Author"},
            {"id": 2, "slug": "item-2", "title": "Item 2"},
        ]

    monkeypatch.setattr(bp, "list_nodes_admin", fake_list_nodes_admin)

    preview = await bp.get_block_preview(
        container,
        "nodes_carousel",
        locale="en",
        limit=2,
    )
    assert preview["source"] == "live"
    assert len(preview["items"]) == 2
    assert preview["items"][0]["title"] == "Item 1"
