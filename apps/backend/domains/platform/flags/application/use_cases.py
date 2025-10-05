from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from ..domain.models import FeatureFlag
from .presenter import (
    build_check_response,
    build_delete_response,
    build_list_response,
    build_upsert_response,
    serialize_flag,
)
from .service import FlagService

logger = logging.getLogger(__name__)


def _safe_effective(
    service: FlagService, flag: FeatureFlag, claims: Mapping[str, Any] | None = None
) -> bool:
    try:
        return bool(service._eval_flag(flag, dict(claims or {})))
    except (RuntimeError, ValueError) as exc:  # pragma: no cover - defensive
        logger.warning("flag_eval_failed", extra={"slug": flag.slug}, exc_info=exc)
        return False


async def list_flags(service: FlagService) -> dict[str, Any]:
    flags = await service.list()
    items = [
        serialize_flag(flag, effective=_safe_effective(service, flag)) for flag in flags
    ]
    return build_list_response(items)


async def upsert_flag(service: FlagService, payload: dict[str, Any]) -> dict[str, Any]:
    flag = await service.upsert(payload)
    effective = _safe_effective(service, flag)
    return build_upsert_response(flag, effective=effective)


async def delete_flag(service: FlagService, slug: str) -> dict[str, Any]:
    await service.delete(slug)
    return build_delete_response()


async def check_flag(
    service: FlagService, slug: str, claims: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    on = await service.evaluate(slug, dict(claims or {}))
    return build_check_response(slug, bool(on))


__all__ = [
    "check_flag",
    "delete_flag",
    "list_flags",
    "upsert_flag",
]
