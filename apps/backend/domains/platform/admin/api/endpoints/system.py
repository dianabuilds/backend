from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from ...service import AdminService
from ..deps import get_admin_service


def register(router: APIRouter) -> None:
    @router.get("/system/overview")
    async def system_overview(
        service: AdminService = Depends(get_admin_service),
    ) -> dict[str, Any]:
        return await service.get_system_overview()
