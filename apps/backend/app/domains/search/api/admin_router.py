from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.audit.application.audit_service import audit_log
from app.domains.search.application.config_service import ConfigService
from app.domains.search.application.stats_service import search_stats
from app.domains.search.infrastructure.repositories.search_config_repository import (
    SearchConfigRepository,
)
from app.providers.db.session import get_db
from app.schemas.search_settings import (
    RelevanceApplyOut,
    RelevanceDryRunOut,
    RelevanceGetOut,
    RelevancePutIn,
    SearchOverviewOut,
)
from app.schemas.search_stats import SearchTopQuery
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

admin_required = require_admin_role({"admin"})  # в MVP только admin применяет

AdminRequired = Annotated[Any, Depends(admin_required)]

router = APIRouter(
    prefix="/admin/search",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.get("/relevance", response_model=RelevanceGetOut, summary="Get active relevance config")
async def get_relevance(
    _: AdminRequired,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> RelevanceGetOut:
    svc = ConfigService(SearchConfigRepository(db))
    return await svc.get_active_relevance()


@router.put("/relevance", summary="Dry-run or apply relevance config")
async def put_relevance(
    body: RelevancePutIn,
    request: Request,
    current: AdminRequired,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
):
    svc = ConfigService(SearchConfigRepository(db))
    if body.dryRun:
        res: RelevanceDryRunOut = await svc.dry_run_relevance(body.payload, body.sample or [])
        return res
    applied: RelevanceApplyOut = await svc.apply_relevance(
        body.payload, str(getattr(current, "id", ""))
    )
    await audit_log(db, actor_id=str(getattr(current, "id", "")), action="search_relevance_update",
                    resource_type="search_config", resource_id=f"relevance:v{applied.version}", before=None,
                    after=body.payload.model_dump(), request=request, extra={"comment": body.comment or ""})
    return applied


@router.post(
    "/relevance/rollback",
    response_model=RelevanceApplyOut,
    summary="Rollback to specified relevance version",
)
async def post_rollback(
    toVersion: int,
    request: Request,
    current: AdminRequired,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> RelevanceApplyOut:
    svc = ConfigService(SearchConfigRepository(db))
    try:
        applied = await svc.rollback_relevance(int(toVersion), str(getattr(current, "id", "")))
    except ValueError as err:
        raise HTTPException(status_code=404, detail="Version not found") from err
    await audit_log(db, actor_id=str(getattr(current, "id", "")), action="search_relevance_rollback",
                    resource_type="search_config", resource_id=f"relevance:v{applied.version}", request=request)
    return applied


@router.get("/overview", response_model=SearchOverviewOut, summary="Search overview KPIs")
async def get_overview(
    _: AdminRequired,
) -> SearchOverviewOut:
    # MVP stub with zeros/empty values
    return SearchOverviewOut(
        activeConfigs={
            "relevance": {"version": 1},
        }
    )


@router.get("/top", response_model=list[SearchTopQuery], summary="Top search queries")
async def get_top(
    _: AdminRequired,
) -> list[SearchTopQuery]:
    return [SearchTopQuery(**item) for item in search_stats.top()]
