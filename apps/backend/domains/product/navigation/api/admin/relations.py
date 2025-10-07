from __future__ import annotations

from app.api_gateway.routers import get_container
from fastapi import APIRouter, Depends, HTTPException, Query

from domains.platform.iam.security import csrf_protect
from domains.product.navigation.application.use_cases.relations_admin import (
    RelationsAdminError,
    RelationsAdminService,
    build_relations_admin_service,
)


def register_admin_relations_routes(router: APIRouter, admin_dependency) -> None:
    """Attach admin relations endpoints to router."""

    async def _get_service(container=Depends(get_container)) -> RelationsAdminService:
        return build_relations_admin_service(container)

    admin_dep = Depends(admin_dependency)

    @router.get("/relations/strategies", dependencies=[admin_dep])
    async def list_strategies(service: RelationsAdminService = Depends(_get_service)):
        return await service.list_strategies()

    @router.patch(
        "/relations/strategies/{strategy}",
        dependencies=[admin_dep, Depends(csrf_protect)],
    )
    async def update_strategy(
        strategy: str,
        payload: dict[str, object],
        service: RelationsAdminService = Depends(_get_service),
    ):
        try:
            return await service.update_strategy(strategy, payload)
        except RelationsAdminError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    @router.get("/relations/overview", dependencies=[admin_dep])
    async def relations_overview(
        service: RelationsAdminService = Depends(_get_service),
    ):
        return await service.overview()

    @router.get("/relations/top", dependencies=[admin_dep])
    async def top_relations(
        algo: str = Query(default="tags"),
        limit: int = Query(default=10, ge=1, le=50),
        service: RelationsAdminService = Depends(_get_service),
    ):
        return await service.top_relations(algo, limit=limit)
