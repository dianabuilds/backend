from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from fastapi import HTTPException

from domains.product.nodes.infrastructure.dev_blog_repository import DevBlogRepository
from domains.product.nodes.infrastructure.engine import ensure_engine
from domains.product.nodes.utils import has_role, normalize_actor_id


class NodesServiceProtocol(Protocol):
    async def _repo_get_async(self, node_id: int): ...

    async def _repo_get_by_slug_async(self, slug: str): ...

    def _to_view(self, dto): ...

    def get_by_slug(self, slug: str): ...


@dataclass
class DevBlogService:
    engine_factory: Callable[[], Awaitable[Any]]
    repository: DevBlogRepository

    async def list_posts(self, *, limit: int, offset: int) -> dict[str, Any]:
        engine = await self.engine_factory()
        if engine is None:
            raise HTTPException(status_code=503, detail="database_unavailable")
        rows, total_count = await self.repository.fetch_page(
            engine, limit=limit, offset=offset
        )
        has_next = offset + len(rows) < total_count
        return {"items": rows, "total": total_count, "has_next": has_next}


@dataclass
class NodeCatalogService:
    nodes_service: NodesServiceProtocol

    async def get_by_ref(
        self, node_ref: str, claims: Mapping[str, Any] | None
    ) -> dict[str, Any]:
        view, _resolved_id = await self._resolve_node_ref(node_ref)
        return self._prepare_view(view, claims)

    def get_by_slug(
        self, slug: str, claims: Mapping[str, Any] | None
    ) -> dict[str, Any]:
        view = self.nodes_service.get_by_slug(slug)
        return self._prepare_view(view, claims)

    async def _resolve_node_ref(self, node_ref: str):
        svc = self.nodes_service
        view = None
        resolved_id: int | None = None
        maybe_id: int | None = None
        try:
            maybe_id = int(node_ref)
        except (TypeError, ValueError):
            maybe_id = None
        if maybe_id is not None:
            dto = await svc._repo_get_async(maybe_id)
            if dto is not None:
                try:
                    resolved_id = int(dto.id)
                except (TypeError, ValueError):
                    resolved_id = None
                else:
                    view = svc._to_view(dto)
        if view is None:
            dto = await svc._repo_get_by_slug_async(str(node_ref))
            if dto is not None:
                try:
                    resolved_id = int(dto.id)
                except (TypeError, ValueError):
                    resolved_id = None
                view = svc._to_view(dto)
        return view, resolved_id

    def _prepare_view(self, view, claims: Mapping[str, Any] | None) -> dict[str, Any]:
        if not view:
            raise HTTPException(status_code=404, detail="not_found")
        if str(view.status or "").lower() == "deleted":
            raise HTTPException(status_code=404, detail="not_found")
        actor_id = normalize_actor_id(claims)
        if (
            view.author_id != actor_id
            and not has_role(claims, "admin")
            and not view.is_public
        ):
            raise HTTPException(status_code=404, detail="not_found")
        return {
            "id": view.id,
            "slug": view.slug,
            "author_id": view.author_id,
            "title": view.title,
            "tags": view.tags,
            "is_public": view.is_public,
            "status": view.status,
            "publish_at": view.publish_at,
            "unpublish_at": view.unpublish_at,
            "content": view.content_html,
            "cover_url": view.cover_url,
            "embedding": view.embedding,
            "views_count": view.views_count,
            "reactions_like_count": view.reactions_like_count,
            "comments_disabled": view.comments_disabled,
            "comments_locked_by": view.comments_locked_by,
            "comments_locked_at": view.comments_locked_at,
        }


def build_dev_blog_service(container: Any) -> DevBlogService:
    async def engine_factory():
        return await ensure_engine(container)

    repository = DevBlogRepository()
    return DevBlogService(engine_factory=engine_factory, repository=repository)


def build_node_catalog_service(container: Any) -> NodeCatalogService:
    return NodeCatalogService(nodes_service=container.nodes_service)
