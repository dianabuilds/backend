from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException

from domains.product.nodes.application.use_cases.helpers import resolve_node_ref
from domains.product.nodes.application.use_cases.ports import NodesServicePort
from domains.product.nodes.domain.results import NodeView
from domains.product.nodes.utils import has_role, normalize_actor_id

DEV_BLOG_TAG = "dev-blog"
DEV_BLOG_MIN_ROLE = "editor"


@dataclass
class CatalogMutationsService:
    nodes_service: NodesServicePort

    async def set_tags(
        self,
        node_ref: str,
        tags: Sequence[str],
        claims: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        view, node_id = await resolve_node_ref(self.nodes_service, node_ref)
        actor_id = self._require_actor(claims)
        self._ensure_owner_or_admin(view, actor_id, claims)
        self._ensure_dev_blog_permissions(
            existing_tags=view.tags,
            new_tags=tags,
            claims=claims,
        )
        updated = await self.nodes_service.update_tags(
            node_id,
            tags,
            actor_id=actor_id,
        )
        return {
            "id": updated.id,
            "tags": updated.tags,
            "embedding": updated.embedding,
        }

    async def create(
        self,
        payload: Mapping[str, Any],
        claims: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        actor_id = self._require_actor(claims)
        title = payload.get("title")
        tags = payload.get("tags")
        self._ensure_dev_blog_permissions(
            existing_tags=None,
            new_tags=tags,
            claims=claims,
        )
        is_public = bool(payload.get("is_public", False))
        status = payload.get("status")
        publish_at = payload.get("publish_at")
        unpublish_at = payload.get("unpublish_at")
        content = payload.get("content") or payload.get("content_html")
        cover_url = payload.get("cover_url")
        view = await self.nodes_service.create(
            author_id=actor_id,
            title=str(title) if title is not None else None,
            tags=tags if isinstance(tags, Sequence) else None,
            is_public=is_public,
            status=str(status) if status else None,
            publish_at=str(publish_at) if publish_at else None,
            unpublish_at=str(unpublish_at) if unpublish_at else None,
            content_html=content,
            cover_url=cover_url,
        )
        return _node_view_to_dict(view)

    async def update(
        self,
        node_ref: str,
        payload: Mapping[str, Any],
        claims: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        view, node_id = await resolve_node_ref(self.nodes_service, node_ref)
        actor_id = self._require_actor(claims)
        self._ensure_owner_or_admin(view, actor_id, claims)
        self._ensure_dev_blog_permissions(
            existing_tags=view.tags,
            new_tags=payload.get("tags"),
            claims=claims,
        )
        view = await self.nodes_service.update(
            node_id,
            title=payload.get("title"),
            is_public=payload.get("is_public"),
            status=(
                str(payload["status"])
                if "status" in payload and payload["status"] is not None
                else None
            ),
            publish_at=(
                str(payload["publish_at"])
                if "publish_at" in payload and payload["publish_at"] is not None
                else None
            ),
            unpublish_at=(
                str(payload["unpublish_at"])
                if "unpublish_at" in payload and payload["unpublish_at"] is not None
                else None
            ),
            content_html=payload.get("content") if "content" in payload else None,
            cover_url=payload.get("cover_url") if "cover_url" in payload else None,
        )
        return _node_view_to_dict(view)

    async def delete(
        self,
        node_ref: str,
        claims: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        view, node_id = await resolve_node_ref(self.nodes_service, node_ref)
        actor_id = self._require_actor(claims)
        self._ensure_owner_or_admin(view, actor_id, claims)
        removed = await self.nodes_service.delete(node_id)
        return {"ok": bool(removed)}

    def _require_actor(self, claims: Mapping[str, Any] | None) -> str:
        actor_id = normalize_actor_id(claims)
        if not actor_id:
            raise HTTPException(status_code=401, detail="unauthorized")
        return actor_id

    def _ensure_owner_or_admin(
        self,
        view: NodeView,
        actor_id: str,
        claims: Mapping[str, Any] | None,
    ) -> None:
        if view.author_id != actor_id and not has_role(claims, "admin"):
            raise HTTPException(status_code=403, detail="forbidden")

    def _ensure_dev_blog_permissions(
        self,
        *,
        existing_tags: Sequence[str] | None,
        new_tags: Any,
        claims: Mapping[str, Any] | None,
    ) -> None:
        if self._uses_dev_blog_tag(existing_tags) or self._uses_dev_blog_tag(new_tags):
            if not has_role(claims, DEV_BLOG_MIN_ROLE):
                raise HTTPException(status_code=403, detail="dev_blog_tag_forbidden")

    @staticmethod
    def _uses_dev_blog_tag(candidate: Any) -> bool:
        if candidate is None:
            return False
        if isinstance(candidate, (str, bytes)):
            return str(candidate).strip().lower() == DEV_BLOG_TAG
        if isinstance(candidate, Sequence):
            return any(
                CatalogMutationsService._uses_dev_blog_tag(item) for item in candidate
            )
        return False


def _node_view_to_dict(view: NodeView) -> dict[str, Any]:
    return {
        "id": view.id,
        "slug": view.slug,
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


def build_catalog_mutations_service(container: Any) -> CatalogMutationsService:
    return CatalogMutationsService(nodes_service=container.nodes_service)
