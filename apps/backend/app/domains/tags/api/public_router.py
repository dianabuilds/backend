from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api import deps as api_deps
from app.domains.tags.models import ContentTag, Tag
from app.domains.users.infrastructure.models.user import User
from app.kernel.db import get_db
from app.schemas.tag import TagOut

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("/", response_model=list[TagOut], summary="List tags")
async def list_tags(
    tenant_id: Annotated[str | None, Query()] = None,  # reserved; ignored for now
    q: Annotated[str | None, Query()] = None,
    popular: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query()] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    current_user: Annotated[User, Depends(api_deps.get_current_user)] = ...,  # noqa: B008
):
    """Retrieve available tags.
    Returns tags used by current user's nodes (profile mode).
    """
    # Profile mode: tags used by current user's nodes
    from app.domains.nodes.infrastructure.models.node import Node
    from app.domains.nodes.models import NodeItem

    stmt = (
        select(Tag, func.count(Node.id).label("count"))
        .join(ContentTag, Tag.id == ContentTag.tag_id)
        .join(NodeItem, NodeItem.id == ContentTag.content_id)
        .join(Node, Node.id == NodeItem.node_id)
        .where(Tag.is_hidden.is_(False), Node.author_id == current_user.id)
    )
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where((Tag.slug.ilike(pattern)) | (Tag.name.ilike(pattern)))
    stmt = stmt.group_by(Tag.id)
    stmt = stmt.order_by(desc("count")) if popular else stmt.order_by(Tag.name)
    stmt = stmt.offset(offset).limit(limit)
    rows = (await db.execute(stmt)).all()
    return [TagOut(slug=t.slug, name=t.name, count=c) for t, c in rows]

