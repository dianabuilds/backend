from __future__ import annotations

from datetime import datetime
from typing import Any, TypedDict

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


class FlagRulePayload(TypedDict):
    type: str
    value: str
    rollout: int | None
    priority: int
    meta: dict[str, Any]


class FlagPayload(TypedDict):
    slug: str
    label: str | None
    description: str | None
    status: str
    status_label: str
    enabled: bool
    effective: bool | None
    audience: str
    rollout: int | None
    release_percent: int | None
    testers: list[str]
    roles: list[str]
    segments: list[str]
    rules: list[FlagRulePayload]
    meta: dict[str, Any]
    created_at: str | None
    updated_at: str | None
    created_by: str | None
    updated_by: str | None


class FlagListResponse(TypedDict):
    items: list[FlagPayload]


class FlagUpsertResponse(TypedDict):
    flag: FlagPayload


class FlagDeleteResponse(TypedDict):
    ok: bool


class FlagCheckResponse(TypedDict):
    slug: str
    on: bool


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


def _serialize_rules(rules: tuple[FlagRule, ...]) -> list[FlagRulePayload]:
    return [
        {
            "type": rule.type.value,
            "value": rule.value,
            "rollout": rule.rollout,
            "priority": rule.priority,
            "meta": dict(rule.meta or {}),
        }
        for rule in rules
    ]


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if isinstance(value, datetime) else None


def serialize_flag(flag: FeatureFlag, *, effective: bool | None = None) -> FlagPayload:
    rollout = flag.rollout if flag.rollout is not None else None
    return {
        "slug": flag.slug,
        "label": feature_label(flag.slug),
        "description": flag.description,
        "status": flag.status.value,
        "status_label": _status_label(flag.status),
        "enabled": flag.status is not FlagStatus.DISABLED,
        "effective": bool(effective) if effective is not None else None,
        "audience": audience_hint(flag),
        "rollout": rollout,
        "release_percent": rollout,
        "testers": sorted(flag.testers),
        "roles": sorted(flag.roles),
        "segments": sorted(flag.segments),
        "rules": _serialize_rules(flag.rules),
        "meta": dict(flag.meta or {}),
        "created_at": _iso(flag.created_at),
        "updated_at": _iso(flag.updated_at),
        "created_by": flag.created_by,
        "updated_by": flag.updated_by,
    }


def build_list_response(items: list[FlagPayload]) -> FlagListResponse:
    return {"items": items}


def build_upsert_response(
    flag: FeatureFlag, *, effective: bool | None = None
) -> FlagUpsertResponse:
    return {"flag": serialize_flag(flag, effective=effective)}


def build_delete_response() -> FlagDeleteResponse:
    return {"ok": True}


def build_check_response(slug: str, on: bool) -> FlagCheckResponse:
    return {"slug": slug, "on": on}


__all__ = [
    "FlagCheckResponse",
    "FlagDeleteResponse",
    "FlagListResponse",
    "FlagPayload",
    "FlagRulePayload",
    "FlagUpsertResponse",
    "audience_hint",
    "build_check_response",
    "build_delete_response",
    "build_list_response",
    "build_upsert_response",
    "feature_label",
    "serialize_flag",
]
