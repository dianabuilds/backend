from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from ...domain.dtos import AIRuleDTO
from ..common import paginate, resolve_iso
from ..presenters.dto_builders import ai_rule_to_dto
from .presenter import (
    build_history_response,
    build_rules_list_response,
    build_test_response,
)

if TYPE_CHECKING:  # pragma: no cover - only for type checking
    from ..service import PlatformModerationService


logger = logging.getLogger(__name__)


async def list_rules(
    service: PlatformModerationService, limit: int = 50, cursor: str | None = None
) -> dict[str, Any]:
    async with service._lock:
        rules = list(service._ai_rules.values())
    rules.sort(
        key=lambda r: r.updated_at or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )
    chunk, next_cursor = paginate(rules, limit, cursor)
    iso = resolve_iso(service)
    dtos = [ai_rule_to_dto(r, iso=iso) for r in chunk]
    return build_rules_list_response(dtos, next_cursor)


async def get_rule(service: PlatformModerationService, rule_id: str) -> AIRuleDTO:
    async with service._lock:
        rule = service._ai_rules.get(rule_id)
        if not rule:
            raise KeyError(rule_id)
        return ai_rule_to_dto(rule, iso=resolve_iso(service))


async def test_rule(
    service: PlatformModerationService, payload: dict[str, Any]
) -> dict[str, Any]:
    rule_id = payload.get("rule_id")
    async with service._lock:
        rule = None
        if rule_id:
            rule = service._ai_rules.get(str(rule_id))
        if not rule and service._ai_rules:
            rule = next(iter(service._ai_rules.values()))
    if not rule:
        return build_test_response(
            payload=payload,
            labels=[],
            scores=payload.get("scores") or payload.get("probabilities") or {},
            decision="pass",
            rule=None,
        )
    scores = payload.get("scores") or payload.get("probabilities") or {}
    labels: list[str] = []
    decision = "pass"
    for label, threshold in rule.thresholds.items():
        try:
            value = float(scores.get(label, 0.0))
        except (TypeError, ValueError) as exc:
            logger.debug(
                "AI moderation score for label %s is invalid (%r): %s",
                label,
                scores.get(label),
                exc,
            )
            value = 0.0
        if value >= float(threshold):
            labels.append(label)
    if labels:
        decision = "flag"
    return build_test_response(
        payload=payload,
        labels=labels,
        scores=scores,
        decision=decision,
        rule=ai_rule_to_dto(rule, iso=resolve_iso(service)),
    )


async def rules_history(
    service: PlatformModerationService, limit: int = 50, cursor: str | None = None
) -> dict[str, Any]:
    async with service._lock:
        history_entries: list[dict[str, Any]] = []
        for rule in service._ai_rules.values():
            for entry in rule.history:
                history_entries.append(
                    {**entry, "rule_id": rule.id, "category": rule.category}
                )
    history_entries.sort(key=lambda e: e.get("updated_at") or "", reverse=True)
    chunk, next_cursor = paginate(history_entries, limit, cursor)
    return build_history_response(chunk, next_cursor)


__all__ = ["get_rule", "list_rules", "rules_history", "test_rule"]
