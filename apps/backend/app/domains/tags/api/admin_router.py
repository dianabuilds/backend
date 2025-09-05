from __future__ import annotations

from typing import Annotated

# ruff: noqa: B008
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.tags.application.tag_admin_service import TagAdminService
from app.domains.tags.infrastructure.repositories.tag_repository import (
    TagRepositoryAdapter,
)
from app.domains.tags.schemas.admin import (
    AliasOut,
    BlacklistAdd,
    BlacklistItem,
    MergeIn,
    MergeReport,
    TagCreate,
    TagListItem,
)
from app.providers.db.session import get_db
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

admin_required = require_admin_role({"admin"})

router = APIRouter(
    prefix="/admin/tags",
    tags=["admin-tags"],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.get(
    "/list",
    response_model=list[TagListItem],
    summary="List tags with usage",
)
async def list_tags(
    q: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 200,
    offset: Annotated[int, Query(ge=0)] = 0,
    _: Annotated[Depends, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> list[TagListItem]:
    svc = TagAdminService(TagRepositoryAdapter(db))
    rows = await svc.list_tags(q, limit, offset)
    return [TagListItem.model_validate(r) for r in rows]


@router.get(
    "/{tag_id}/aliases",
    response_model=list[AliasOut],
    summary="List tag aliases",
)
async def get_aliases(
    tag_id: UUID,
    _: Annotated[Depends, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> list[AliasOut]:
    svc = TagAdminService(TagRepositoryAdapter(db))
    items = await svc.list_aliases(tag_id)
    return [AliasOut.model_validate(x) for x in items]


@router.post("/{tag_id}/aliases", response_model=AliasOut, summary="Add tag alias")
async def post_alias(
    tag_id: UUID,
    alias: str,
    request: Request,
    current=Depends(admin_required),
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> AliasOut:
    svc = TagAdminService(TagRepositoryAdapter(db))
    item = await svc.add_alias(db, tag_id, alias, str(getattr(current, "id", "")), request)
    return AliasOut.model_validate(item)


@router.delete("/aliases/{alias_id}", summary="Remove tag alias")
async def del_alias(
    alias_id: UUID,
    request: Request,
    current=Depends(admin_required),
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    svc = TagAdminService(TagRepositoryAdapter(db))
    await svc.remove_alias(db, alias_id, str(getattr(current, "id", "")), None, request)
    return {"ok": True}


@router.post(
    "/merge",
    response_model=MergeReport,
    summary="Merge tags (dry-run/apply)",
)
async def merge_tags(
    body: MergeIn,
    request: Request,
    current=Depends(admin_required),
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> MergeReport:
    svc = TagAdminService(TagRepositoryAdapter(db))
    if body.dryRun:
        report = await svc.dry_run_merge(body.from_id, body.to_id)
        return MergeReport.model_validate(report)
    report = await svc.apply_merge(
        db,
        body.from_id,
        body.to_id,
        str(getattr(current, "id", "")),
        body.reason,
        request,
    )
    return MergeReport.model_validate(report)


@router.get(
    "/blacklist",
    response_model=list[BlacklistItem],
    summary="List blacklisted tags",
)
async def get_blacklist(
    q: Annotated[str | None, Query()] = None,
    _: Annotated[Depends, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> list[BlacklistItem]:
    svc = TagAdminService(TagRepositoryAdapter(db))
    items = await svc.blacklist_list(q)
    return [BlacklistItem.model_validate(r) for r in items]


@router.post(
    "/blacklist",
    response_model=BlacklistItem,
    summary="Add tag to blacklist",
)
async def add_blacklist(
    body: BlacklistAdd,
    request: Request,
    current=Depends(admin_required),
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> BlacklistItem:
    svc = TagAdminService(TagRepositoryAdapter(db))
    item = await svc.blacklist_add(
        db,
        (body.slug or "").strip(),
        body.reason,
        str(getattr(current, "id", "")),
        request,
    )
    return BlacklistItem.model_validate(item)


@router.delete("/blacklist/{slug}", summary="Remove tag from blacklist")
async def delete_blacklist(
    slug: str,
    request: Request,
    current=Depends(admin_required),
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    svc = TagAdminService(TagRepositoryAdapter(db))
    await svc.blacklist_delete(db, slug, str(getattr(current, "id", "")), request)
    return {"ok": True}


@router.post("/", response_model=TagListItem, summary="Create tag")
async def create_tag(
    body: TagCreate,
    request: Request,
    current=Depends(admin_required),
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> TagListItem:
    svc = TagAdminService(TagRepositoryAdapter(db))
    slug = (body.slug or "").strip().lower()
    name = (body.name or "").strip()
    if not slug or not name:
        raise HTTPException(status_code=400, detail="Slug and name are required")
    # check blacklist inside the repo layer
    # create
    tag = await svc.create_tag(db, slug, name, str(getattr(current, "id", "")), request)
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
    current=Depends(admin_required),
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
):
    svc = TagAdminService(TagRepositoryAdapter(db))
    await svc.delete_tag(db, tag_id, str(getattr(current, "id", "")), request)
    return {"ok": True}
