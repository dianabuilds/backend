from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request

try:
    from fastapi_limiter.depends import RateLimiter  # type: ignore
except ImportError:  # pragma: no cover
    RateLimiter = None  # type: ignore


from apps.backend import get_container
from domains.platform.iam.security import csrf_protect, require_admin
from domains.product.tags.adapters.admin_repo_sql import (
    create_repo as create_admin_repo,
)
from domains.product.tags.application.admin_service import TagAdminService

logger = logging.getLogger(__name__)


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/admin/tags", tags=["admin-tags"])

    def _svc(container) -> TagAdminService:
        cached = getattr(container, "_tags_admin_service", None)
        if cached is not None:
            return cached
        usage_store = None
        try:
            repo0 = getattr(getattr(container, "tags_service", None), "repo", None)
            usage_store = getattr(repo0, "store", None)
        except AttributeError as exc:
            logger.debug("tag_admin_usage_store_unavailable", exc_info=exc)
        repo = create_admin_repo(container.settings, store=usage_store)
        service = TagAdminService(repo, outbox=container.events.outbox)
        container._tags_admin_service = service
        return service

    @router.get("/groups", summary="List tag content groups")
    def list_groups(
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ):
        svc = _svc(container)
        groups = svc.list_groups()
        return [
            {
                "key": g.key,
                "tag_count": g.tag_count,
                "usage_count": g.usage_count,
                "author_count": g.author_count,
            }
            for g in groups
        ]

    @router.get("/list", summary="List tags with usage")
    def list_tags(
        q: str | None = Query(default=None),
        limit: int = Query(ge=1, le=1000, default=200),
        offset: int = Query(ge=0, default=0),
        type_: str | None = Query(default="all"),
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ):
        svc = _svc(container)
        ctype = (type_ or "all").lower()
        if ctype not in ("all", "node", "quest"):
            ctype = "all"
        rows = svc.list_tags(q, limit, offset, content_type=ctype)
        return [
            {
                "id": r.id,
                "slug": r.slug,
                "name": r.name,
                "created_at": r.created_at,
                "usage_count": r.usage_count,
                "aliases_count": r.aliases_count,
                "is_hidden": r.is_hidden,
            }
            for r in rows
        ]

    @router.get("/{tag_id}/aliases", summary="List tag aliases")
    def get_aliases(
        tag_id: UUID, _: None = Depends(require_admin), container=Depends(get_container)
    ):
        svc = _svc(container)
        items = svc.list_aliases(str(tag_id))
        return [
            {
                "id": a.id,
                "alias": a.alias,
                "type": a.type,
                "created_at": a.created_at,
            }
            for a in items
        ]

    @router.post(
        "/{tag_id}/aliases",
        summary="Add tag alias",
        dependencies=(
            [Depends(RateLimiter(times=30, seconds=60))] if RateLimiter else []
        ),
    )
    def post_alias(
        tag_id: UUID,
        alias: str,
        request: Request,
        _: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
        container=Depends(get_container),
    ):
        try:
            svc = _svc(container)
            item = svc.add_alias(str(tag_id), alias)
            return {
                "id": item.id,
                "alias": item.alias,
                "type": item.type,
                "created_at": item.created_at,
            }
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e)) from e

    @router.get("/blacklist", summary="List blacklisted tags")
    def get_blacklist(
        q: str | None = Query(default=None),
        _: None = Depends(require_admin),
        container=Depends(get_container),
    ):
        svc = _svc(container)
        items = svc.blacklist_list(q)
        return [
            {"slug": i.slug, "reason": i.reason, "created_at": i.created_at}
            for i in items
        ]

    @router.post(
        "/blacklist",
        summary="Add tag to blacklist",
        dependencies=(
            [Depends(RateLimiter(times=30, seconds=60))] if RateLimiter else []
        ),
    )
    def add_blacklist(
        payload: dict,
        request: Request,
        _: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
        container=Depends(get_container),
    ):
        slug = (payload.get("slug") or "").strip()
        reason = payload.get("reason")
        if not slug:
            raise HTTPException(status_code=400, detail="slug_required")
        svc = _svc(container)
        item = svc.blacklist_add(slug, reason)
        return {"slug": item.slug, "reason": item.reason, "created_at": item.created_at}

    @router.delete(
        "/blacklist/{slug}",
        summary="Remove tag from blacklist",
        dependencies=(
            [Depends(RateLimiter(times=30, seconds=60))] if RateLimiter else []
        ),
    )
    def delete_blacklist(
        slug: str,
        request: Request,
        _: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
        container=Depends(get_container),
    ):
        svc = _svc(container)
        svc.blacklist_delete(slug)
        return {"ok": True}

    @router.post(
        "",
        summary="Create tag",
        dependencies=(
            [Depends(RateLimiter(times=20, seconds=60))] if RateLimiter else []
        ),
    )
    def create_tag(
        body: dict,
        request: Request,
        _: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
        container=Depends(get_container),
    ):
        slug = (body.get("slug") or "").strip()
        name = (body.get("name") or "").strip()
        if not slug or not name:
            raise HTTPException(status_code=400, detail="slug_and_name_required")
        try:
            svc = _svc(container)
            t = svc.create_tag(slug, name)
            return {
                "id": t.id,
                "slug": t.slug,
                "name": t.name,
                "created_at": t.created_at,
                "usage_count": t.usage_count,
                "aliases_count": t.aliases_count,
                "is_hidden": t.is_hidden,
            }
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e)) from e

    @router.delete(
        "/{tag_id}",
        summary="Delete tag",
        dependencies=(
            [Depends(RateLimiter(times=20, seconds=60))] if RateLimiter else []
        ),
    )
    def delete_tag(
        tag_id: UUID,
        request: Request,
        _: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
        container=Depends(get_container),
    ):
        svc = _svc(container)
        svc.delete_tag(str(tag_id))
        return {"ok": True}

    @router.post(
        "/merge",
        summary="Merge tags (dry-run/apply)",
        dependencies=(
            [Depends(RateLimiter(times=10, seconds=60))] if RateLimiter else []
        ),
    )
    def merge_tags(
        body: dict,
        request: Request,
        _: None = Depends(require_admin),
        _csrf: None = Depends(csrf_protect),
        container=Depends(get_container),
    ):
        from_id = body.get("from_id")
        to_id = body.get("to_id")
        dry = bool(body.get("dryRun"))
        reason = body.get("reason")
        type_ = str(body.get("type") or "all").lower()
        if type_ not in ("all", "node", "quest"):
            type_ = "all"
        if not from_id or not to_id:
            raise HTTPException(status_code=400, detail="from_id_and_to_id_required")
        svc = _svc(container)
        if dry:
            return svc.merge_dry_run(str(from_id), str(to_id), content_type=type_)
        return svc.merge_apply(
            str(from_id), str(to_id), None, reason, content_type=type_
        )

    return router
