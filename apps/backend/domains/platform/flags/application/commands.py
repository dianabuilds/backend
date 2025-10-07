from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .presenter import (
    FlagDeleteResponse,
    FlagUpsertResponse,
    build_delete_response,
    build_upsert_response,
)
from .service import FlagService


async def upsert_flag(
    service: FlagService, payload: Mapping[str, Any]
) -> FlagUpsertResponse:
    flag = await service.upsert(payload)
    effective = service.effective(flag)
    return build_upsert_response(flag, effective=effective)


async def delete_flag(service: FlagService, slug: str) -> FlagDeleteResponse:
    await service.delete(slug)
    return build_delete_response()


__all__ = ["delete_flag", "upsert_flag"]
