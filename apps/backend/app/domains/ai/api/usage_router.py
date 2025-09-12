from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.infrastructure.repositories.usage_repository import (
    AIUsageRepository,
)
from app.kernel.db import get_db
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

admin_required = require_admin_role({"admin"})

router = APIRouter(
    prefix="/admin/ai/usage",
    tags=["admin-ai-usage"],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.get("/system", summary="System-wide usage totals")
async def get_system_usage(
    _: Annotated[object, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> dict:
    repo = AIUsageRepository(db)
    return await repo.system_totals()


# Only system-wide totals are exposed in this build.

