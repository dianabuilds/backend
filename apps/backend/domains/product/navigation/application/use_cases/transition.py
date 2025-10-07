from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from domains.product.navigation.application.ports import TransitionRequest
from domains.product.navigation.domain.transition import (
    TransitionCandidate,
    TransitionDecision,
)


class NavigationTransitionService(Protocol):
    """Minimum contract required from navigation service."""

    def next(self, data: TransitionRequest) -> TransitionDecision: ...


class TransitionError(Exception):
    """Base error for transition use-case."""

    def __init__(self, detail: str, *, status_code: int) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class TransitionUnauthorizedError(TransitionError):
    def __init__(self, detail: str = "unauthorized") -> None:
        super().__init__(detail, status_code=401)


class TransitionValidationError(TransitionError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail, status_code=400)


@dataclass(frozen=True)
class TransitionCommand:
    body: Mapping[str, Any]
    claims: Mapping[str, Any] | None = None
    session_id_header: str | None = None
    session_id_cookie: str | None = None


@dataclass(frozen=True)
class TransitionResult:
    payload: dict[str, Any]
    decision: TransitionDecision | None = None


class TransitionHandler:
    """Prepare transition request and orchestrate navigation service call."""

    def __init__(self, service: NavigationTransitionService) -> None:
        self._service = service
        self._logger = logging.getLogger(__name__)

    def execute(self, command: TransitionCommand) -> TransitionResult:
        claims = command.claims or {}
        user_id = str(claims.get("sub") or "")
        if not user_id:
            raise TransitionUnauthorizedError()

        body = dict(command.body)
        session_id = self._extract_session_id(body, command)
        origin_node_id = self._parse_optional_int(
            body.get("origin_node_id"), "invalid_origin_node_id"
        )
        route_window = self._parse_int_sequence(
            body.get("route_window"), "invalid_route_window"
        )
        requested_slots = self._parse_optional_int(
            body.get("ui_slots"), "invalid_ui_slots", default=0
        )
        provider_overrides = self._parse_provider_overrides(
            body.get("requested_provider_overrides")
        )
        limit_state = str(body.get("limit_state") or "normal")
        mode = str(body.get("mode") or "normal")
        premium_level = str(
            body.get("premium_level") or claims.get("premium_level") or "free"
        )
        policies_hash_raw = body.get("policies_hash")
        policies_hash = (
            str(policies_hash_raw) if policies_hash_raw is not None else None
        )
        emergency = bool(body.get("emergency"))

        transition = TransitionRequest(
            user_id=user_id,
            session_id=session_id,
            origin_node_id=origin_node_id,
            route_window=route_window,
            limit_state=limit_state,
            mode=mode,
            requested_ui_slots=requested_slots,
            premium_level=premium_level,
            policies_hash=policies_hash,
            requested_provider_overrides=provider_overrides,
            emergency=emergency,
        )

        decision = self._service.next(transition)
        payload = self._build_payload(decision, requested_slots)
        return TransitionResult(payload=payload, decision=decision)

    def _extract_session_id(
        self, body: Mapping[str, Any], command: TransitionCommand
    ) -> str:
        session_id_raw = body.get("session_id")
        if not session_id_raw:
            session_id_raw = (
                command.session_id_header or command.session_id_cookie or ""
            )
        session_id = str(session_id_raw or "")
        if not session_id:
            raise TransitionValidationError("session_id_required")
        return session_id

    def _parse_optional_int(
        self, value: Any, error_detail: str, *, default: int | None = None
    ) -> int | None:
        if value is None:
            return default
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise TransitionValidationError(error_detail) from exc

    def _parse_int_sequence(self, value: Any, error_detail: str) -> tuple[int, ...]:
        if value is None:
            return ()
        if not isinstance(value, (list, tuple)):
            raise TransitionValidationError(error_detail)
        try:
            return tuple(int(item) for item in value if item is not None)
        except (TypeError, ValueError) as exc:
            raise TransitionValidationError(error_detail) from exc

    def _parse_provider_overrides(self, value: Any) -> tuple[str, ...]:
        if value is None:
            return ()
        if not isinstance(value, (list, tuple)):
            return ()
        return tuple(str(item) for item in value if isinstance(item, str))

    def _build_payload(
        self, decision: TransitionDecision, requested_slots: int | None
    ) -> dict[str, Any]:
        requested_echo = (
            requested_slots
            if requested_slots is not None and requested_slots > 0
            else decision.context.requested_ui_slots
        )
        payload: dict[str, Any] = {
            "query_id": f"q-{decision.context.cache_seed[:12]}",
            "ui_slots_requested": requested_echo,
            "ui_slots": decision.ui_slots_granted,
            "limit_state": decision.limit_state,
            "mode": decision.mode,
            "emergency_used": decision.emergency_used,
            "decision": {
                "candidates": [
                    self._candidate_payload(item) for item in decision.candidates
                ],
                "curated_blocked_reason": decision.curated_blocked_reason,
                "empty_pool": decision.empty_pool,
                "empty_pool_reason": decision.empty_pool_reason,
                "served_from_cache": decision.served_from_cache,
            },
            "pool_size": decision.pool_size,
            "cache_seed": decision.context.cache_seed,
            "t": decision.temperature,
            "epsilon": decision.epsilon,
            "mode_applied": decision.mode,
            "telemetry": dict(decision.telemetry),
        }
        if decision.empty_pool:
            payload["fallback_suggestions"] = [
                "open_search",
                "open_map",
                "resume_trail",
            ]
        return payload

    def _candidate_payload(self, item: TransitionCandidate) -> dict[str, Any]:
        return {
            "id": item.node_id,
            "badge": item.badge,
            "score": round(item.score, 4),
            "probability": round(item.probability, 4),
            "reason": {
                key: round(float(value), 4) for key, value in item.factors.items()
            },
            "explain": item.explain,
            "provider": item.provider,
        }


def build_transition_handler(container: Any) -> TransitionHandler:
    """Lightweight factory to keep container knowledge outside HTTP layer."""

    service = container.navigation_service
    return TransitionHandler(service)
