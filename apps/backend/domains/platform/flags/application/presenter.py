from __future__ import annotations

from datetime import datetime
from typing import Any

from ..domain.models import FeatureFlag, FlagRule, FlagStatus

_FEATURE_FLAGS = {
    "nodes": "content.nodes",
    "quests": "content.quests",
    "notifications": "notifications.broadcasts",
    "billing": "billing.revenue",
    "observability": "observability.core",
    "moderation": "moderation.guardrails",
}

_FEATURE_LABELS = {value: key for key, value in _FEATURE_FLAGS.items()}


def feature_label(slug: str) -> str | None:
    if not slug:
        return None
    direct = _FEATURE_LABELS.get(slug)
    if direct:
        return direct
    for nice, candidate in _FEATURE_FLAGS.items():
        if candidate == slug:
            return nice
    return slug.split(".")[-1]


def audience_hint(flag: FeatureFlag) -> str:
    if flag.status is FlagStatus.ALL:
        return "all"
    if flag.status is FlagStatus.PREMIUM:
        return "premium"
    if flag.status is FlagStatus.TESTERS or flag.testers:
        return "testers"
    if flag.status is FlagStatus.CUSTOM or flag.roles or flag.segments or flag.rules:
        return "custom"
    if flag.status is FlagStatus.DISABLED:
        return "disabled"
    return flag.status.value


def _status_label(status: FlagStatus) -> str:
    match status:
        case FlagStatus.DISABLED:
            return "disabled"
        case FlagStatus.TESTERS:
            return "testers"
        case FlagStatus.PREMIUM:
            return "premium"
        case FlagStatus.ALL:
            return "all"
        case FlagStatus.CUSTOM:
            return "custom"
    return status.value


def _serialize_rules(rules: tuple[FlagRule, ...]) -> list[dict[str, Any]]:
    return [
        {
            "type": rule.type.value,
            "value": rule.value,
            "rollout": rule.rollout,
            "priority": rule.priority,
            "meta": rule.meta or {},
        }
        for rule in rules
    ]


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if isinstance(value, datetime) else None


def serialize_flag(
    flag: FeatureFlag, *, effective: bool | None = None
) -> dict[str, Any]:
    return {
        "slug": flag.slug,
        "label": feature_label(flag.slug),
        "description": flag.description,
        "status": flag.status.value,
        "status_label": _status_label(flag.status),
        "enabled": flag.status is not FlagStatus.DISABLED,
        "effective": bool(effective) if effective is not None else None,
        "audience": audience_hint(flag),
        "rollout": flag.rollout,
        "release_percent": flag.rollout,
        "testers": sorted(flag.testers),
        "roles": sorted(flag.roles),
        "segments": sorted(flag.segments),
        "rules": _serialize_rules(flag.rules),
        "meta": flag.meta or {},
        "created_at": _iso(flag.created_at),
        "updated_at": _iso(flag.updated_at),
        "created_by": flag.created_by,
        "updated_by": flag.updated_by,
    }


def build_list_response(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {"items": items}


def build_upsert_response(
    flag: FeatureFlag, *, effective: bool | None = None
) -> dict[str, Any]:
    return {"flag": serialize_flag(flag, effective=effective)}


def build_delete_response() -> dict[str, Any]:
    return {"ok": True}


def build_check_response(slug: str, on: bool) -> dict[str, Any]:
    return {"slug": slug, "on": on}


__all__ = [
    "audience_hint",
    "build_check_response",
    "build_delete_response",
    "build_list_response",
    "build_upsert_response",
    "feature_label",
    "serialize_flag",
]
