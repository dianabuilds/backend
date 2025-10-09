from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from ..deps import get_public_use_cases


def register(router: APIRouter) -> None:
    @router.get("/plans")
    async def list_plans(use_cases=Depends(get_public_use_cases)) -> dict[str, Any]:
        return await use_cases.list_plans()
