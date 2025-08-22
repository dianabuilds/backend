from __future__ import annotations

from sqlalchemy import func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import APIRouter, Depends, Query

from app.db.session import get_db
from app.domains.tags.infrastructure.models.tag_models import Tag, NodeTag
from app.schemas.tag import TagOut

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("/", response_model=list[TagOut], summary="List tags")
async def list_tags(
    q: str | None = Query(None),
    popular: bool = Query(False),
    limit: int = Query(10),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve available tags with optional search and popularity filter."""
    stmt = (
        select(Tag, func.count(NodeTag.node_id).label("count"))
        .join(NodeTag, Tag.id == NodeTag.tag_id, isouter=True)
        .where(Tag.is_hidden == False)
    )
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where((Tag.slug.ilike(pattern)) | (Tag.name.ilike(pattern)))
    stmt = stmt.group_by(Tag.id)
    if popular:
        stmt = stmt.order_by(desc("count"))
    else:
        stmt = stmt.order_by(Tag.name)
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    rows = result.all()
    return [TagOut(slug=t.slug, name=t.name, count=c) for t, c in rows]
