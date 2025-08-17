from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.models.tag import Tag, NodeTag
from app.security import require_admin_role, ADMIN_AUTH_RESPONSES

admin_required = require_admin_role()

router = APIRouter(
    prefix="/admin/tags",
    tags=["admin-tags"],
    dependencies=[Depends(admin_required)],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.get("", summary="List tags (admin)")
async def list_tags_admin(
    q: str | None = Query(None, description="Search by slug or name"),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Return tags for admin UI with usage counters.
    Supports optional search and simple pagination.
    """
    stmt = (
        select(Tag, func.count(NodeTag.node_id).label("usage_count"))
        .join(NodeTag, Tag.id == NodeTag.tag_id, isouter=True)
        .group_by(Tag.id)
    )
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where((Tag.slug.ilike(pattern)) | (Tag.name.ilike(pattern)))
    stmt = stmt.order_by(desc("usage_count"), Tag.name).offset(offset).limit(limit)
    res = await db.execute(stmt)
    rows = res.all()
    # Возвращаем поля, ожидаемые админкой
    return [
        {
            "id": str(tag.id),
            "slug": tag.slug,
            "name": tag.name,
            "created_at": tag.created_at,
            "usage_count": int(usage or 0),
            "is_hidden": bool(tag.is_hidden),
        }
        for tag, usage in rows
    ]
