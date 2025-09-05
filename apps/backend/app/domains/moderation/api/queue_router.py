from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.moderation.application import CasesService
from app.providers.db.session import get_db
from app.schemas.moderation_cases import CaseListResponse
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

cases_service = CasesService()
admin_required = require_admin_role()

router = APIRouter(
    prefix="/admin/moderation",
    tags=["admin"],
    dependencies=[Depends(admin_required)],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.get("/queue", response_model=CaseListResponse)
async def list_queue(
    page: int = 1,
    size: int = 20,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,  # noqa: B008
) -> CaseListResponse:
    return await cases_service.list_cases(
        db, page=page, size=size, statuses=["new", "in_progress"]
    )
