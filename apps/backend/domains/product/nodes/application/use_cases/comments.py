from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException

from domains.product.nodes.application.use_cases.helpers import resolve_node_ref
from domains.product.nodes.application.use_cases.ports import NodesServicePort
from domains.product.nodes.domain.results import NodeView
from domains.product.nodes.utils import (
    comment_ban_to_dict,
    comment_to_dict,
    has_role,
    normalize_actor_id,
)


@dataclass
class CommentsService:
    nodes_service: NodesServicePort

    async def list_comments(
        self,
        node_ref: str,
        *,
        parent_comment_id: int | None,
        limit: int,
        offset: int,
        include_deleted: bool,
        claims: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        view, node_id = await resolve_node_ref(self.nodes_service, node_ref)
        actor_id = normalize_actor_id(claims)
        allow_deleted = include_deleted and (
            has_role(claims, "moderator") or view.author_id == actor_id
        )
        if include_deleted and not allow_deleted:
            raise HTTPException(status_code=403, detail="insufficient_role")
        comments = await self.nodes_service.list_comments(
            node_id,
            parent_comment_id=parent_comment_id,
            limit=limit,
            offset=offset,
            include_deleted=allow_deleted,
        )
        return {
            "items": [comment_to_dict(item) for item in comments],
            "count": len(comments),
        }

    async def create_comment(
        self,
        node_ref: str,
        payload: Mapping[str, Any],
        claims: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        _, node_id = await resolve_node_ref(self.nodes_service, node_ref)
        actor_id = self._require_actor(claims)
        content = payload.get("content")
        if not isinstance(content, str) or not content.strip():
            raise HTTPException(status_code=400, detail="content_required")
        parent_comment_id = payload.get("parent_comment_id") or payload.get("parentId")
        if parent_comment_id is not None:
            try:
                parent_comment_id = int(parent_comment_id)
            except (TypeError, ValueError):
                raise HTTPException(
                    status_code=400, detail="parent_id_invalid"
                ) from None
        metadata = payload.get("metadata")
        if metadata is not None and not isinstance(metadata, Mapping):
            raise HTTPException(status_code=400, detail="metadata_invalid")
        try:
            comment = await self.nodes_service.create_comment(
                node_id=node_id,
                author_id=actor_id,
                content=content,
                parent_comment_id=parent_comment_id,
                metadata=dict(metadata) if isinstance(metadata, Mapping) else None,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return comment_to_dict(comment)

    async def delete_comment(
        self,
        comment_id: int,
        *,
        hard: bool,
        reason: str | None,
        claims: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        comment = await self.nodes_service.get_comment(comment_id)
        if comment is None:
            raise HTTPException(status_code=404, detail="not_found")
        node_view = await self._get_node_view(comment.node_id)
        actor_id = self._require_actor(claims)
        if not self._can_delete_comment(comment, node_view, actor_id, claims):
            raise HTTPException(status_code=403, detail="forbidden")
        removed = await self.nodes_service.delete_comment(
            comment_id,
            actor_id=actor_id,
            hard=hard,
            reason=reason,
        )
        return {"ok": bool(removed)}

    async def update_comment_status(
        self,
        comment_id: int,
        payload: Mapping[str, Any],
        claims: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        if not has_role(claims, "moderator"):
            raise HTTPException(status_code=403, detail="insufficient_role")
        status = payload.get("status")
        if not isinstance(status, str) or not status.strip():
            raise HTTPException(status_code=400, detail="status_required")
        reason = payload.get("reason")
        actor_id = normalize_actor_id(claims)
        try:
            updated = await self.nodes_service.update_comment_status(
                comment_id,
                status=status,
                actor_id=actor_id or None,
                reason=reason,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return comment_to_dict(updated)

    async def toggle_comments_lock(
        self,
        node_ref: str,
        payload: Mapping[str, Any],
        claims: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        view, node_id = await resolve_node_ref(self.nodes_service, node_ref)
        actor_id = self._require_actor(claims)
        self._ensure_author_or_moderator(view, actor_id, claims)
        locked = bool(payload.get("locked", True))
        reason = payload.get("reason")
        if locked:
            await self.nodes_service.lock_comments(
                node_id, actor_id=actor_id, reason=reason
            )
        else:
            await self.nodes_service.unlock_comments(node_id, actor_id=actor_id)
        return {"id": node_id, "locked": locked}

    async def toggle_comments_disabled(
        self,
        node_ref: str,
        payload: Mapping[str, Any],
        claims: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        view, node_id = await resolve_node_ref(self.nodes_service, node_ref)
        actor_id = self._require_actor(claims)
        self._ensure_author_or_moderator(view, actor_id, claims)
        disabled = bool(payload.get("disabled", True))
        reason = payload.get("reason")
        if disabled:
            await self.nodes_service.disable_comments(
                node_id, actor_id=actor_id, reason=reason
            )
        else:
            await self.nodes_service.enable_comments(
                node_id, actor_id=actor_id, reason=reason
            )
        return {"id": node_id, "disabled": disabled}

    async def ban_comment_user(
        self,
        node_ref: str,
        payload: Mapping[str, Any],
        claims: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        view, node_id = await resolve_node_ref(self.nodes_service, node_ref)
        actor_id = self._require_actor(claims)
        self._ensure_author_or_moderator(view, actor_id, claims)
        target_user_id = payload.get("target_user_id") or payload.get("targetUserId")
        if not isinstance(target_user_id, str) or not target_user_id.strip():
            raise HTTPException(status_code=400, detail="target_user_id_required")
        reason = payload.get("reason")
        ban = await self.nodes_service.ban_comment_user(
            node_id,
            target_user_id=target_user_id.strip(),
            actor_id=actor_id,
            reason=reason,
        )
        return comment_ban_to_dict(ban)

    async def unban_comment_user(
        self,
        node_ref: str,
        target_user_id: str,
        claims: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        view, node_id = await resolve_node_ref(self.nodes_service, node_ref)
        actor_id = self._require_actor(claims)
        self._ensure_author_or_moderator(view, actor_id, claims)
        ok = await self.nodes_service.unban_comment_user(node_id, target_user_id)
        return {"ok": bool(ok)}

    async def list_comment_bans(
        self,
        node_ref: str,
        claims: Mapping[str, Any] | None,
    ) -> list[dict[str, Any]]:
        view, node_id = await resolve_node_ref(self.nodes_service, node_ref)
        actor_id = normalize_actor_id(claims)
        if view.author_id != actor_id and not has_role(claims, "moderator"):
            raise HTTPException(status_code=403, detail="forbidden")
        bans = await self.nodes_service.list_comment_bans(node_id)
        return [comment_ban_to_dict(item) for item in bans]

    async def _get_node_view(self, node_id: int) -> NodeView:
        dto = await self.nodes_service._repo_get_async(node_id)
        if dto is None:
            raise HTTPException(status_code=404, detail="node_not_found")
        return self.nodes_service._to_view(dto)

    def _require_actor(self, claims: Mapping[str, Any] | None) -> str:
        actor_id = normalize_actor_id(claims)
        if not actor_id:
            raise HTTPException(status_code=401, detail="unauthorized")
        return actor_id

    def _ensure_author_or_moderator(
        self,
        view: NodeView,
        actor_id: str,
        claims: Mapping[str, Any] | None,
    ) -> None:
        if view.author_id != actor_id and not has_role(claims, "moderator"):
            raise HTTPException(status_code=403, detail="forbidden")

    def _can_delete_comment(
        self,
        comment,
        node_view: NodeView,
        actor_id: str,
        claims: Mapping[str, Any] | None,
    ) -> bool:
        if comment.author_id == actor_id:
            return True
        if node_view.author_id == actor_id:
            return True
        return has_role(claims, "moderator")


def build_comments_service(container: Any) -> CommentsService:
    return CommentsService(nodes_service=container.nodes_service)
