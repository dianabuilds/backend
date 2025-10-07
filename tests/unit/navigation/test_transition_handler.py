from __future__ import annotations

from datetime import UTC, datetime

import pytest

from domains.product.navigation.application.use_cases.transition import (
    TransitionCommand,
    TransitionHandler,
    TransitionUnauthorizedError,
)
from domains.product.navigation.domain.transition import (
    TransitionCandidate,
    TransitionContext,
    TransitionDecision,
)


class StubNavigationService:
    def __init__(self, decision: TransitionDecision) -> None:
        self.decision = decision
        self.calls: list = []

    def next(self, data):
        self.calls.append(data)
        return self.decision


def build_decision() -> TransitionDecision:
    context = TransitionContext(
        session_id="session-from-decision",
        user_id="user-1",
        origin_node_id=42,
        route_window=(1, 2),
        limit_state="lim",
        premium_level="gold",
        mode="mode-x",
        requested_ui_slots=3,
        policies_hash="hash",
        cache_seed="seed1234567890",
        created_at=datetime.now(UTC),
    )
    candidate = TransitionCandidate(
        node_id=99,
        provider="tags",
        score=0.9,
        probability=0.8,
        factors={"base": 0.7},
        badge="top",
        explain="reason",
    )
    return TransitionDecision(
        context=context,
        candidates=(candidate,),
        selected_node_id=99,
        ui_slots_granted=3,
        limit_state="lim",
        mode="mode-x",
        pool_size=5,
        temperature=0.5,
        epsilon=0.1,
        empty_pool=False,
        empty_pool_reason=None,
        curated_blocked_reason=None,
        served_from_cache=False,
        emergency_used=False,
        telemetry={"base": 0.3},
    )


def test_execute_returns_payload_and_calls_service():
    decision = build_decision()
    service = StubNavigationService(decision)
    handler = TransitionHandler(service)
    command = TransitionCommand(
        body={
            "origin_node_id": "42",
            "route_window": [1, "2", None],
            "ui_slots": 4,
            "requested_provider_overrides": ["foo", 123],
            "limit_state": "lim",
            "mode": "mode-x",
            "premium_level": "gold",
            "policies_hash": 321,
            "emergency": True,
        },
        claims={"sub": "user-1", "premium_level": "silver"},
        session_id_header="header-session",
        session_id_cookie="cookie-session",
    )

    result = handler.execute(command)

    assert service.calls, "service.next was not invoked"
    transition_request = service.calls[0]
    assert transition_request.user_id == "user-1"
    assert transition_request.session_id == "header-session"
    assert transition_request.origin_node_id == 42
    assert transition_request.route_window == (1, 2)
    assert transition_request.requested_ui_slots == 4
    assert transition_request.requested_provider_overrides == ("foo",)
    assert transition_request.policies_hash == "321"
    assert transition_request.emergency is True
    assert transition_request.mode == "mode-x"
    assert transition_request.premium_level == "gold"

    assert result.payload["ui_slots_requested"] == 4
    candidate = result.payload["decision"]["candidates"][0]
    assert candidate["id"] == 99
    assert candidate["provider"] == "tags"


def test_execute_requires_user_id():
    handler = TransitionHandler(StubNavigationService(build_decision()))
    command = TransitionCommand(body={})

    with pytest.raises(TransitionUnauthorizedError):
        handler.execute(command)
