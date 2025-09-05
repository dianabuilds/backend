from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.domains.admin.infrastructure.models.audit_log import AuditLog
from app.domains.users.infrastructure.models.user import User
from app.providers.db.session import get_db
from app.schemas.audit import AuditLogOut
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

admin_only = require_admin_role({"admin"})

router = APIRouter(
    prefix="/admin/audit",
    tags=["admin"],
    dependencies=[Depends(admin_only)],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.get("", response_model=list[AuditLogOut], summary="List audit logs")
async def list_audit_logs(
    actor_id: UUID | None = None,
    action: str | None = None,
    resource: str | None = None,
    workspace_id: UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
    current_user: Annotated[User, Depends(admin_only)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    stmt = select(AuditLog)
    if actor_id:
        stmt = stmt.where(AuditLog.actor_id == actor_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if resource:
        stmt = stmt.where(
            or_(AuditLog.resource_type == resource, AuditLog.resource_id == resource)
        )
    if workspace_id:
        stmt = stmt.where(AuditLog.workspace_id == workspace_id)
    if date_from:
        stmt = stmt.where(AuditLog.created_at >= date_from)
    if date_to:
        stmt = stmt.where(AuditLog.created_at <= date_to)
    stmt = stmt.order_by(AuditLog.created_at.desc())
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)
    result = await db.execute(stmt)
    return result.scalars().all()
