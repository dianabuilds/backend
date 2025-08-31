from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.domains.admin.application.jobs_service import JobsService
from app.schemas.job import BackgroundJobHistoryOut
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

admin_required = require_admin_role({"admin", "support"})

router = APIRouter(
    prefix="/admin/jobs",
    tags=["admin"],
    dependencies=[Depends(admin_required)],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.get(
    "/recent",
    summary="Get recent background jobs",
    response_model=list[BackgroundJobHistoryOut],
)
async def recent_jobs(
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[BackgroundJobHistoryOut]:
    jobs = await JobsService.get_recent(db, limit=10)
    return [BackgroundJobHistoryOut.model_validate(j) for j in jobs]
