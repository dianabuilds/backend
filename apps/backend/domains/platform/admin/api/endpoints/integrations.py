from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from ...service import AdminService
from ..deps import get_admin_service


def register(router: APIRouter) -> None:
    @router.get("/integrations")
    async def integrations(
        service: AdminService = Depends(get_admin_service),
    ) -> dict[str, Any]:
        return service.get_integrations()
