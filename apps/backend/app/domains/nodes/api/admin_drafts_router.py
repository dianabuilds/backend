from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.application.node_query_service import NodeQueryService
from app.providers.db.session import get_db
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(
    prefix="/admin/drafts", tags=["admin"], responses=ADMIN_AUTH_RESPONSES
)
admin_required = require_admin_role()


@router.get("/issues", summary="List drafts with missing fields")
async def list_draft_issues(
    _: Annotated[object, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    limit: int = 5,
):
    svc = NodeQueryService(db)
    return await svc.list_drafts_with_issues(limit=limit)
