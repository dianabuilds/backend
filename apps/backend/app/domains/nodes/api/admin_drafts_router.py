from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.session import get_db
from app.domains.nodes.application.node_query_service import NodeQueryService
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

router = APIRouter(prefix="/admin/drafts", tags=["admin"], responses=ADMIN_AUTH_RESPONSES)
admin_required = require_admin_role()

@router.get("/issues", summary="List drafts with missing fields")
async def list_draft_issues(
    _: object = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
    limit: int = 5,
):
    svc = NodeQueryService(db)
    items = await svc.list_drafts_with_issues(limit=limit)
    return [
        {
            "id": str(node.id),
            "slug": node.slug,
            "title": node.title,
            "issues": issues,
        }
        for node, issues in items
    ]
