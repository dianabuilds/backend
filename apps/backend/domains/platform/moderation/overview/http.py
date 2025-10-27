from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from apps.backend.app.api_gateway.routers import get_container

from ..domain.dtos import OverviewDTO
from ..rbac import require_scopes

router = APIRouter(prefix="/overview", tags=["moderation-overview"])


@router.get(
    "",
    response_model=OverviewDTO,
    dependencies=[Depends(require_scopes("moderation:overview:read"))],
)
async def get_overview(
    limit: int = Query(default=10, ge=1, le=50),
    container=Depends(get_container),
) -> OverviewDTO:
    """Return aggregated moderation overview metrics for the dashboard."""
    svc = container.platform_moderation.service
    result = await svc.get_overview(limit=limit)
    if isinstance(result, OverviewDTO):
        return result
    return OverviewDTO.model_validate(result)


__all__ = ["router", "get_overview"]
