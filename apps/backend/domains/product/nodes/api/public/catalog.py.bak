from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request

from apps.backend.app.api_gateway.routers import get_container
from domains.platform.iam.application.facade import get_current_user, require_role_db
from domains.product.nodes.application.use_cases.catalog import (
    DevBlogService,
    NodeCatalogService,
    build_dev_blog_service,
    build_node_catalog_service,
)


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        try:
            return datetime.fromisoformat(f"{text}T00:00:00")
        except ValueError:
            return None


def register_catalog_routes(router: APIRouter) -> None:
    @router.get("", summary="List nodes for current actor")
    async def list_nodes(
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        author_id: str | None = Query(default=None),
        service: NodeCatalogService = Depends(_get_catalog_service),
        claims=Depends(get_current_user),
    ):
        return service.list_nodes(
            claims=claims,
            author_id=author_id,
            limit=int(limit),
            offset=int(offset),
        )

    @router.get("/dev-blog", summary="List public dev blog posts")
    async def list_dev_blog_posts(
        limit: int = Query(default=12, ge=1, le=50),
        offset: int = Query(default=0, ge=0),
        tags: list[str] = Query(default=[]),
        published_from: str | None = Query(default=None, alias="from"),
        published_to: str | None = Query(default=None, alias="to"),
        service: DevBlogService = Depends(_get_dev_blog_service),
    ):
        parsed_from = _parse_iso_datetime(published_from)
        parsed_to = _parse_iso_datetime(published_to)
        normalized_tags = [
            tag.strip() for tag in tags if isinstance(tag, str) and tag.strip()
        ]
        return await service.list_posts(
            limit=int(limit),
            offset=int(offset),
            tags=normalized_tags or None,
            published_from=parsed_from,
            published_to=parsed_to,
        )

    @router.get("/dev-blog/{slug}", summary="Get public dev blog post")
    async def get_dev_blog_post(
        slug: str,
        service: DevBlogService = Depends(_get_dev_blog_service),
    ):
        post, sort_value = await service.get_post_by_slug(slug, preview=False)
        adjacent = await service.get_adjacent_posts(
            sort_value=sort_value, node_id=post.get("id")
        )
        return {"post": post, "prev": adjacent["prev"], "next": adjacent["next"]}

    @router.get(
        "/dev-blog/{slug}/preview",
        summary="Preview dev blog post",
        dependencies=[Depends(require_role_db("editor"))],
    )
    async def preview_dev_blog_post(
        slug: str,
        service: DevBlogService = Depends(_get_dev_blog_service),
    ):
        post, sort_value = await service.get_post_by_slug(slug, preview=True)
        adjacent = await service.get_adjacent_posts(
            sort_value=sort_value, node_id=post.get("id")
        )
        return {"post": post, "prev": adjacent["prev"], "next": adjacent["next"]}

    @router.get("/{node_id}")
    async def get_node(
        node_id: str,
        req: Request,
        service: NodeCatalogService = Depends(_get_catalog_service),
        claims=Depends(get_current_user),
    ):
        return await service.get_by_ref(node_id, claims)

    @router.get("/slug/{slug}")
    def get_node_by_slug(
        slug: str,
        req: Request,
        service: NodeCatalogService = Depends(_get_catalog_service),
        claims=Depends(get_current_user),
    ):
        return service.get_by_slug(slug, claims)


def _get_dev_blog_service(container=Depends(get_container)) -> DevBlogService:
    return build_dev_blog_service(container)


def _get_catalog_service(container=Depends(get_container)) -> NodeCatalogService:
    return build_node_catalog_service(container)
