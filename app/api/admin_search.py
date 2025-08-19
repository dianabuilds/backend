from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.search_settings import (
    RelevanceGetOut,
    RelevancePutIn,
    RelevanceApplyOut,
    RelevanceDryRunOut,
    SearchOverviewOut,
)
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role
from app.services.search_config import (
    get_active_relevance,
    dry_run_relevance,
    apply_relevance,
    rollback_relevance,
)
from app.services.audit import audit_log

admin_required = require_admin_role({"admin"})  # в MVP только admin применяет

router = APIRouter(
    prefix="/admin/search",
    tags=["admin"],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.get("/relevance", response_model=RelevanceGetOut, summary="Get active relevance config")
async def get_relevance(_: Depends = Depends(admin_required), db: AsyncSession = Depends(get_db)) -> RelevanceGetOut:
    return await get_active_relevance(db)


@router.put("/relevance", summary="Dry-run or apply relevance config")
async def put_relevance(
    body: RelevancePutIn,
    request: Request,
    current = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    if body.dryRun:
        res = await dry_run_relevance(db, body.payload, body.sample or [])
        return res
    # apply
    applied = await apply_relevance(db, body.payload, str(getattr(current, "id", "")))
    await audit_log(
        db,
        actor_id=str(getattr(current, "id", "")),
        action="search_relevance_update",
        resource_type="search_config",
        resource_id=f"relevance:v{applied.version}",
        before=None,
        after=body.payload.model_dump(),
        request=request,
        extra={"comment": body.comment or ""},
    )
    return applied


@router.post("/relevance/rollback", response_model=RelevanceApplyOut, summary="Rollback to specified relevance version")
async def post_rollback(
    toVersion: int,
    request: Request,
    current = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
) -> RelevanceApplyOut:
    try:
        applied = await rollback_relevance(db, int(toVersion), str(getattr(current, "id", "")))
    except ValueError:
        raise HTTPException(status_code=404, detail="Version not found")
    await audit_log(
        db,
        actor_id=str(getattr(current, "id", "")),
        action="search_relevance_rollback",
        resource_type="search_config",
        resource_id=f"relevance:v{applied.version}",
        request=request,
    )
    return applied


@router.get("/overview", response_model=SearchOverviewOut, summary="Search overview KPIs")
async def get_overview(_: Depends = Depends(admin_required)) -> SearchOverviewOut:
    # MVP stub with zeros/empty values
    return SearchOverviewOut(
        activeConfigs={
            "relevance": {"version": 1},
        }
    )
