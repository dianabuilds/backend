from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.domains.admin.application.dashboard_service import DashboardService
from app.domains.users.infrastructure.models.user import User
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(prefix="/admin", tags=["admin"], responses=ADMIN_AUTH_RESPONSES)
admin_required = require_admin_role()

current_user_dep = Depends(admin_required)
db_dep = Depends(get_db)


@router.get("/dashboard", summary="Admin dashboard data")
async def admin_dashboard(
    current_user: User = current_user_dep,
    db: AsyncSession = db_dep,
):
    return await DashboardService.get_dashboard(db)
