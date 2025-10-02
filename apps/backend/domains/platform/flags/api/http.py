from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

try:
    from fastapi_limiter.depends import RateLimiter  # type: ignore
except Exception:  # pragma: no cover
    RateLimiter = None  # type: ignore

from apps.backend import get_container
from domains.platform.flags.domain.models import FeatureFlag, FlagStatus
from domains.platform.iam.security import (
    csrf_protect,
    get_current_user,
    require_admin,
)

_FEATURE_FLAGS = {
    "nodes": "content.nodes",
    "quests": "content.quests",
    "notifications": "notifications.broadcasts",
    "billing": "billing.revenue",
    "observability": "observability.core",
    "moderation": "moderation.guardrails",
}


_FEATURE_LABELS = {value: key for key, value in _FEATURE_FLAGS.items()}


def _audience_hint(flag: FeatureFlag) -> str:
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


def _feature_label(slug: str) -> str | None:
    labels = globals().get("_FEATURE_LABELS")
    if isinstance(labels, dict):
        result = labels.get(slug)
        if result is not None:
            return result
    for nice, candidate in globals().get("_FEATURE_FLAGS", {}).items():
        if candidate == slug:
            return nice
    return slug.split(".")[-1] if slug else None


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/flags", tags=["flags"])

    @router.get(
        "",
        dependencies=([Depends(RateLimiter(times=60, seconds=60))] if RateLimiter else []),
    )
    async def list_flags(req: Request, _admin: None = Depends(require_admin)) -> dict[str, Any]:
        c = get_container(req)
        items = await c.flags.service.list()
        response: list[dict[str, Any]] = []
        for flag in items:
            try:
                effective_value = bool(c.flags.service._eval_flag(flag, {}))
            except Exception:
                effective_value = False
            response.append(_serialize_flag(flag, effective=effective_value))
        return {"items": response}

    @router.post(
        "",
        dependencies=([Depends(RateLimiter(times=20, seconds=60))] if RateLimiter else []),
    )
    async def upsert_flag(
        req: Request,
        body: dict[str, Any],
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        if not isinstance(body, dict):
            raise HTTPException(status_code=400, detail="invalid_payload")
        if "slug" not in body:
            raise HTTPException(status_code=400, detail="slug_required")
        c = get_container(req)
        try:
            flag = await c.flags.service.upsert(body)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        try:
            effective_value = bool(c.flags.service._eval_flag(flag, {}))
        except Exception:
            effective_value = False
        return {"flag": _serialize_flag(flag, effective=effective_value)}

    @router.delete(
        "/{slug}",
        dependencies=([Depends(RateLimiter(times=20, seconds=60))] if RateLimiter else []),
    )
    async def delete_flag(
        req: Request,
        slug: str,
        _admin: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
    ) -> dict[str, Any]:
        c = get_container(req)
        await c.flags.service.delete(slug)
        return {"ok": True}

    @router.get("/check/{slug}")
    async def check_flag(
        req: Request, slug: str, claims=Depends(get_current_user)
    ) -> dict[str, Any]:
        c = get_container(req)
        on = await c.flags.service.evaluate(slug, claims or {})
        return {"slug": slug, "on": bool(on)}

    return router


def _serialize_flag(flag: FeatureFlag, *, effective: bool | None = None) -> dict[str, Any]:
    return {
        "slug": flag.slug,
        "label": _feature_label(flag.slug),
        "description": flag.description,
        "status": flag.status.value,
        "status_label": _status_label(flag.status),
        "enabled": flag.status is not FlagStatus.DISABLED,
        "effective": bool(effective) if effective is not None else None,
        "audience": _audience_hint(flag),
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
    }


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


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if isinstance(value, datetime) else None


__all__ = ["make_router"]
