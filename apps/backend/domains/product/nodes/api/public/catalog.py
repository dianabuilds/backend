from __future__ import annotations

from app.api_gateway.routers import get_container
from fastapi import APIRouter, Depends, Query, Request

from domains.platform.iam.security import get_current_user
from domains.product.nodes.application.use_cases.catalog import (
    DevBlogService,
    NodeCatalogService,
    build_dev_blog_service,
    build_node_catalog_service,
)


def register_catalog_routes(router: APIRouter) -> None:
    @router.get("/dev-blog", summary="List public dev blog posts")
    async def list_dev_blog_posts(
        limit: int = Query(default=12, ge=1, le=50),
        offset: int = Query(default=0, ge=0),
        service: DevBlogService = Depends(_get_dev_blog_service),
    ):
        return await service.list_posts(limit=int(limit), offset=int(offset))

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
