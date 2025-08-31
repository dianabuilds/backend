from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role
from app.schemas.job import BackgroundJobHistoryOut
from app.domains.admin.application.jobs_service import JobsService

admin_required = require_admin_role()

router = APIRouter(
    prefix="/admin/jobs",
    tags=["admin"],
    dependencies=[Depends(admin_required)],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.get("/recent", summary="Get recent background jobs", response_model=list[BackgroundJobHistoryOut])
async def recent_jobs(db: AsyncSession = Depends(get_db)) -> list[BackgroundJobHistoryOut]:
    jobs = await JobsService.get_recent(db, limit=10)
    return [BackgroundJobHistoryOut.model_validate(j) for j in jobs]
