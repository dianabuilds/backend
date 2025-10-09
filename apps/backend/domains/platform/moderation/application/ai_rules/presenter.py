from __future__ import annotations

from typing import Any

from ...domain.dtos import AIRuleDTO
from ..presenters import build_list_response


def build_rules_list_response(
    items: list[AIRuleDTO], next_cursor: str | None
) -> dict[str, Any]:
    return build_list_response(items, next_cursor=next_cursor)


def build_history_response(
    items: list[dict[str, Any]], next_cursor: str | None
) -> dict[str, Any]:
    return build_list_response(items, next_cursor=next_cursor)


def build_test_response(
    *,
    payload: dict[str, Any],
    labels: list[str],
    scores: dict[str, Any],
    decision: str,
    rule: AIRuleDTO | None,
) -> dict[str, Any]:
    response: dict[str, Any] = {
        "input": payload,
        "labels": labels,
        "scores": scores,
        "decision": decision,
    }
    if rule is not None:
        response["rule"] = rule
    return response


__all__ = [
    "build_history_response",
    "build_rules_list_response",
    "build_test_response",
]
