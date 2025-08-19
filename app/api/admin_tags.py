from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy import func, select, desc, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.tag import Tag, NodeTag
from app.models.tag_extras import TagAlias, TagBlacklist
from app.schemas.tags_admin import TagListItem, AliasOut, MergeIn, MergeReport, BlacklistItem, BlacklistAdd
from app.schemas.tag import TagCreate
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role
from app.services.tags_admin import add_alias, remove_alias, list_aliases, dry_run_merge, apply_merge
from app.services.audit import audit_log

admin_required = require_admin_role({"admin"})

router = APIRouter(
    prefix="/admin/tags",
    tags=["admin-tags"],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.get("/list", response_model=List[TagListItem], summary="List tags with usage")
async def list_tags(
    q: str | None = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    _: Depends = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
) -> List[TagListItem]:
    stmt = (
        select(
            Tag,
            func.count(NodeTag.node_id).label("usage_count"),
            func.count(TagAlias.id).label("aliases_count"),
        )
        .join(NodeTag, Tag.id == NodeTag.tag_id, isouter=True)
        .join(TagAlias, Tag.id == TagAlias.tag_id, isouter=True)
        .group_by(Tag.id)
    )
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where((Tag.slug.ilike(pattern)) | (Tag.name.ilike(pattern)))
    stmt = stmt.order_by(desc("usage_count"), Tag.name).offset(offset).limit(limit)
    res = await db.execute(stmt)
    rows = res.all()
    return [
        TagListItem.model_validate(
            {
                "id": tag.id,
                "slug": tag.slug,
                "name": tag.name,
                "created_at": tag.created_at,
                "usage_count": int(usage or 0),
                "aliases_count": int(aliases or 0),
                "is_hidden": bool(tag.is_hidden),
            }
        )
        for tag, usage, aliases in rows
    ]


@router.get("/{tag_id}/aliases", response_model=List[AliasOut], summary="List tag aliases")
async def get_aliases(
    tag_id: UUID,
    _: Depends = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
) -> List[AliasOut]:
    items = await list_aliases(db, tag_id)
    return [AliasOut.model_validate(x) for x in items]


@router.post("/{tag_id}/aliases", response_model=AliasOut, summary="Add tag alias")
async def post_alias(
    tag_id: UUID,
    alias: str,
    request: Request,
    current = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
) -> AliasOut:
    item = await add_alias(db, tag_id, alias)
    await audit_log(
        db,
        actor_id=str(getattr(current, "id", "")),
        action="tag_alias_add",
        resource_type="tag",
        resource_id=str(tag_id),
        after={"alias": item.alias},
        request=request,
    )
    await db.commit()
    return AliasOut.model_validate(item)


@router.delete("/aliases/{alias_id}", summary="Remove tag alias")
async def del_alias(
    alias_id: UUID,
    request: Request,
    current = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    a = await db.get(TagAlias, alias_id)
    if not a:
        raise HTTPException(status_code=404, detail="Alias not found")
    await remove_alias(db, alias_id)
    await audit_log(
        db,
        actor_id=str(getattr(current, "id", "")),
        action="tag_alias_remove",
        resource_type="tag",
        resource_id=str(a.tag_id),
        before={"alias": a.alias},
        request=request,
    )
    await db.commit()
    return {"ok": True}


@router.post("/merge", response_model=MergeReport, summary="Merge tags (dry-run/apply)")
async def merge_tags(
    body: MergeIn,
    request: Request,
    current = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
) -> MergeReport:
    if body.dryRun:
        report = await dry_run_merge(db, body.from_id, body.to_id)
        return MergeReport.model_validate(report)
    report = await apply_merge(db, body.from_id, body.to_id, str(getattr(current, "id", "")), body.reason)
    await audit_log(
        db,
        actor_id=str(getattr(current, "id", "")),
        action="tag_merge_apply",
        resource_type="tag",
        resource_id=f"{body.from_id}->{body.to_id}",
        after=report,
        request=request,
        reason=body.reason or None,
    )
    await db.commit()
    return MergeReport.model_validate(report)


@router.get("/blacklist", response_model=List[BlacklistItem], summary="List blacklisted tags")
async def get_blacklist(
    q: str | None = Query(None),
    _: Depends = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
) -> List[BlacklistItem]:
    stmt = select(TagBlacklist)
    if q:
        stmt = stmt.where(TagBlacklist.slug.ilike(f"%{q}%"))
    stmt = stmt.order_by(TagBlacklist.created_at.desc())
    rows = (await db.execute(stmt)).scalars().all()
    return [BlacklistItem.model_validate(r) for r in rows]


@router.post("/blacklist", response_model=BlacklistItem, summary="Add tag to blacklist")
async def add_blacklist(
    body: BlacklistAdd,
    request: Request,
    current = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
) -> BlacklistItem:
    slug = (body.slug or "").strip()
    if not slug:
        raise HTTPException(status_code=400, detail="Slug is required")
    exists = await db.get(TagBlacklist, slug)
    if exists:
        return BlacklistItem.model_validate(exists)
    item = TagBlacklist(slug=slug, reason=body.reason)
    db.add(item)
    await db.flush()
    await audit_log(
        db,
        actor_id=str(getattr(current, "id", "")),
        action="tag_blacklist_add",
        resource_type="tag_blacklist",
        resource_id=slug,
        after={"slug": slug, "reason": body.reason},
        request=request,
    )
    await db.commit()
    return BlacklistItem.model_validate(item)


@router.delete("/blacklist/{slug}", summary="Remove tag from blacklist")
async def delete_blacklist(
    slug: str,
    request: Request,
    current = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    item = await db.get(TagBlacklist, slug)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(item)
    await audit_log(
        db,
        actor_id=str(getattr(current, "id", "")),
        action="tag_blacklist_remove",
        resource_type="tag_blacklist",
        resource_id=slug,
        before={"slug": slug, "reason": item.reason},
        request=request,
    )
    await db.commit()
    return {"ok": True}


@router.post("/", response_model=TagListItem, summary="Create tag")
async def create_tag(
    body: TagCreate,
    request: Request,
    current = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
) -> TagListItem:
    slug = (body.slug or "").strip()
    name = (body.name or "").strip()
    if not slug or not name:
        raise HTTPException(status_code=400, detail="Slug and name are required")
    # Check blacklist
    in_blacklist = await db.get(TagBlacklist, slug)
    if in_blacklist:
        raise HTTPException(status_code=400, detail="Slug is blacklisted")
    # Check duplicate
    existing = await db.execute(select(Tag).where(Tag.slug == slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Tag already exists")
    tag = Tag(slug=slug, name=name)
    db.add(tag)
    await db.flush()
    await audit_log(
        db,
        actor_id=str(getattr(current, "id", "")),
        action="tag_create",
        resource_type="tag",
        resource_id=str(tag.id),
        after={"id": str(tag.id), "slug": tag.slug, "name": tag.name},
        request=request,
    )
    await db.commit()
    return TagListItem.model_validate(
        {
            "id": tag.id,
            "slug": tag.slug,
            "name": tag.name,
            "created_at": tag.created_at,
            "usage_count": 0,
            "aliases_count": 0,
            "is_hidden": bool(tag.is_hidden),
        }
    )


@router.delete("/{tag_id}", summary="Delete tag")
async def delete_tag(
    tag_id: UUID,
    request: Request,
    current = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    tag = await db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    # Remove aliases and relations before deleting the tag
    await db.execute(delete(TagAlias).where(TagAlias.tag_id == tag_id))
    await db.execute(delete(NodeTag).where(NodeTag.tag_id == tag_id))
    before = {"id": str(tag.id), "slug": tag.slug, "name": tag.name, "is_hidden": bool(tag.is_hidden)}
    await db.delete(tag)
    await audit_log(
        db,
        actor_id=str(getattr(current, "id", "")),
        action="tag_delete",
        resource_type="tag",
        resource_id=str(tag_id),
        before=before,
        request=request,
    )
    await db.commit()
    return {"ok": True}
