from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from domains.product.nodes.application.ports import (
    NodeCommentBanDTO,
    NodeCommentDTO,
    NodeCommentsRepo,
)


@dataclass
class CommentsRepository:
    repo: NodeCommentsRepo

    async def list_for_node(
        self,
        node_id: int,
        *,
        parent_comment_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> list[NodeCommentDTO]:
        return await self.repo.list_for_node(
            node_id,
            parent_comment_id=parent_comment_id,
            limit=limit,
            offset=offset,
            include_deleted=include_deleted,
        )

    async def create(
        self,
        *,
        node_id: int,
        author_id: str,
        content: str,
        parent_comment_id: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> NodeCommentDTO:
        return await self.repo.create(
            node_id=node_id,
            author_id=author_id,
            content=content,
            parent_comment_id=parent_comment_id,
            metadata=metadata,
        )

    async def get(self, comment_id: int) -> NodeCommentDTO | None:
        return await self.repo.get(comment_id)

    async def delete(
        self,
        comment_id: int,
        *,
        actor_id: str,
        hard: bool = False,
        reason: str | None = None,
    ) -> bool:
        if hard:
            return await self.repo.hard_delete(comment_id)
        return await self.repo.soft_delete(
            comment_id,
            actor_id=actor_id,
            reason=reason,
        )

    async def update_status(
        self,
        comment_id: int,
        *,
        status: str,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> NodeCommentDTO:
        return await self.repo.update_status(
            comment_id,
            status=status,
            actor_id=actor_id,
            reason=reason,
        )

    async def lock(
        self,
        node_id: int,
        *,
        locked_by: str | None,
        locked_at: str | None,
        reason: str | None = None,
    ) -> None:
        await self.repo.lock_node(
            node_id,
            locked_by=locked_by,
            locked_at=locked_at,
            reason=reason,
        )

    async def set_disabled(
        self,
        node_id: int,
        *,
        disabled: bool,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> None:
        await self.repo.set_comments_disabled(
            node_id,
            disabled=disabled,
            actor_id=actor_id,
            reason=reason,
        )

    async def ban_user(
        self,
        node_id: int,
        *,
        target_user_id: str,
        set_by: str,
        reason: str | None = None,
    ) -> NodeCommentBanDTO:
        return await self.repo.record_ban(
            node_id,
            target_user_id,
            set_by=set_by,
            reason=reason,
        )

    async def unban_user(self, node_id: int, target_user_id: str) -> bool:
        return await self.repo.remove_ban(node_id, target_user_id)

    async def is_banned(self, node_id: int, target_user_id: str) -> bool:
        return await self.repo.is_banned(node_id, target_user_id)

    async def list_bans(self, node_id: int) -> list[NodeCommentBanDTO]:
        return await self.repo.list_bans(node_id)
