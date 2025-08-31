from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.db.session import get_db
from app.domains.tags.dao import TagDAO
from app.domains.tags.models import ContentTag, Tag
from app.schemas.tag import TagCreate, TagOut, TagUpdate
from app.security import require_ws_editor, require_ws_guest

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("/", response_model=list[TagOut], summary="List tags")
async def list_tags(
    workspace_id: UUID,
    q: str | None = Query(None),
    popular: bool = Query(False),
    limit: int = Query(10),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: object = Depends(require_ws_guest),
):
    """Retrieve available tags with optional search and popularity filter."""
    stmt = (
        select(Tag, func.count(ContentTag.content_id).label("count"))
        .join(ContentTag, Tag.id == ContentTag.tag_id, isouter=True)
        .where(
            Tag.is_hidden.is_(False),
            Tag.workspace_id == workspace_id,
            (ContentTag.workspace_id == workspace_id) | (ContentTag.tag_id.is_(None)),
        )
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


@router.post("/", response_model=TagOut, summary="Create tag")
async def create_tag(
    workspace_id: UUID,
    body: TagCreate,
    _: object = Depends(require_ws_editor),
    db: AsyncSession = Depends(get_db),
) -> TagOut:
    tag = await TagDAO.create(
        db, workspace_id=workspace_id, slug=body.slug, name=body.name
    )
    return TagOut(slug=tag.slug, name=tag.name, count=0)


@router.get("/{slug}", response_model=TagOut, summary="Get tag")
async def get_tag(
    workspace_id: UUID,
    slug: str,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(require_ws_guest),
) -> TagOut:
    tag = await TagDAO.get_by_slug(db, workspace_id=workspace_id, slug=slug)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    count = await TagDAO.usage_count(db, tag.id, workspace_id)
    return TagOut(slug=tag.slug, name=tag.name, count=count)


@router.put("/{slug}", response_model=TagOut, summary="Update tag")
async def update_tag(
    workspace_id: UUID,
    slug: str,
    body: TagUpdate,
    _: object = Depends(require_ws_editor),
    db: AsyncSession = Depends(get_db),
) -> TagOut:
    tag = await TagDAO.get_by_slug(db, workspace_id=workspace_id, slug=slug)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    if body.name is not None:
        tag.name = body.name
    if body.hidden is not None:
        tag.is_hidden = body.hidden
    db.add(tag)
    await db.flush()
    count = await TagDAO.usage_count(db, tag.id, workspace_id)
    return TagOut(slug=tag.slug, name=tag.name, count=count)


@router.delete("/{slug}", summary="Delete tag")
async def delete_tag(
    workspace_id: UUID,
    slug: str,
    _: object = Depends(require_ws_editor),
    db: AsyncSession = Depends(get_db),
):
    tag = await TagDAO.get_by_slug(db, workspace_id=workspace_id, slug=slug)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    await TagDAO.detach_all(db, tag.id, workspace_id)
    await TagDAO.delete(db, tag)
    return {"ok": True}
