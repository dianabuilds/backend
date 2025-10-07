from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .presenter import (
    FlagCheckResponse,
    FlagListResponse,
    build_check_response,
    build_list_response,
    serialize_flag,
)
from .service import FlagService


async def list_flags(service: FlagService) -> FlagListResponse:
    flags = await service.list()
    items = [serialize_flag(flag, effective=service.effective(flag)) for flag in flags]
    return build_list_response(items)


async def check_flag(
    service: FlagService, slug: str, claims: Mapping[str, Any] | None = None
) -> FlagCheckResponse:
    on = await service.evaluate(slug, claims)
    return build_check_response(slug, bool(on))


__all__ = ["check_flag", "list_flags"]
