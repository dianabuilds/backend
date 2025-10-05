from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Request, Response

from domains.platform.flags.domain.models import FeatureFlag, FlagStatus
from domains.platform.iam.security import get_current_user
from packages.core.settings_contract import attach_settings_schema

from ..idempotency import IDEMPOTENCY_HEADER
from ..routers import get_container

logger = logging.getLogger(__name__)

_FEATURE_FLAGS = {
    "content_nodes": "content.nodes",
    "content_quests": "content.quests",
    "notifications_broadcasts": "notifications.broadcasts",
    "billing_revenue": "billing.revenue",
    "observability_core": "observability.core",
    "moderation_guardrails": "moderation.guardrails",
}


_FEATURE_LABELS = {value: key for key, value in _FEATURE_FLAGS.items()}


def _feature_label(slug: str) -> str | None:
    if slug in _FEATURE_LABELS:
        return _FEATURE_LABELS[slug]
    for feature_key, feature_slug in _FEATURE_FLAGS.items():
        if feature_slug == slug:
            return feature_key
    return None


async def _resolve_features(
    request: Request, user_claims: dict[str, Any] | None
) -> dict[str, Any]:
    container = get_container(request)
    svc = container.flags.service
    claims = user_claims or {}
    result: dict[str, Any] = {}
    for feature_key, flag_slug in _FEATURE_FLAGS.items():
        evaluated_at = datetime.now(UTC)
        try:
            flag = await svc.get(flag_slug)
        except Exception as exc:
            logger.exception("Failed to fetch feature flag %s", flag_slug, exc_info=exc)
            flag = None
        try:
            effective = bool(await svc.evaluate(flag_slug, claims))
        except Exception as exc:
            logger.exception(
                "Failed to evaluate feature flag %s", flag_slug, exc_info=exc
            )
            effective = False
        if flag is None:
            result[feature_key] = _missing_feature(flag_slug, effective, evaluated_at)
            continue
        result[feature_key] = _serialize_feature(
            flag, effective=effective, evaluated_at=evaluated_at
        )
    return result


async def _features_payload(
    request: Request,
    response: Response,
    claims: dict[str, Any] | None,
) -> dict[str, Any]:
    features = await _resolve_features(request, claims)
    payload = {"features": features, "idempotency_header": IDEMPOTENCY_HEADER}
    attach_settings_schema(payload, response)
    return payload


def _serialize_feature(
    flag: FeatureFlag, *, effective: bool, evaluated_at: datetime
) -> dict[str, Any]:
    return {
        "slug": flag.slug,
        "label": _feature_label(flag.slug),
        "description": flag.description,
        "status": flag.status.value,
        "status_label": _status_label(flag.status),
        "enabled": flag.status is not FlagStatus.DISABLED,
        "effective": effective,
        "rollout": flag.rollout,
        "release_percent": flag.rollout,
        "testers": sorted(flag.testers),
        "roles": sorted(flag.roles),
        "segments": sorted(flag.segments),
        "rules": [
            {
                "type": rule.type.value,
                "value": rule.value,
                "rollout": rule.rollout,
                "priority": rule.priority,
                "meta": rule.meta or {},
            }
            for rule in flag.rules
        ],
        "meta": flag.meta or {},
        "created_at": _iso(flag.created_at),
        "updated_at": _iso(flag.updated_at),
        "evaluated_at": _iso(evaluated_at),
    }


def _missing_feature(
    slug: str, effective: bool, evaluated_at: datetime
) -> dict[str, Any]:
    return {
        "slug": slug,
        "label": _feature_label(slug),
        "status": "missing",
        "status_label": "missing",
        "enabled": False,
        "effective": effective,
        "rollout": None,
        "release_percent": None,
        "testers": [],
        "roles": [],
        "segments": [],
        "rules": [],
        "meta": {},
        "created_at": None,
        "updated_at": None,
        "evaluated_at": _iso(evaluated_at),
        "error": "flag_missing",
    }


def _status_label(status: FlagStatus) -> str:
    if status is FlagStatus.DISABLED:
        return "disabled"
    if status is FlagStatus.TESTERS:
        return "testers"
    if status is FlagStatus.PREMIUM:
        return "premium"
    if status is FlagStatus.ALL:
        return "all"
    if status is FlagStatus.CUSTOM:
        return "custom"
    return status.value


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if isinstance(value, datetime) else None


def register(admin_router: APIRouter, personal_router: APIRouter) -> None:
    @admin_router.get("/features")
    async def settings_features(
        request: Request,
        response: Response,
        claims=Depends(get_current_user),
    ) -> dict[str, Any]:
        return await _features_payload(request, response, claims)

    @personal_router.get("/features")
    async def me_settings_features(
        request: Request,
        response: Response,
        claims=Depends(get_current_user),
    ) -> dict[str, Any]:
        return await _features_payload(request, response, claims)


__all__ = ["register"]
