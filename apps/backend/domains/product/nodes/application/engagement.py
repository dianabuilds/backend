from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from domains.product.nodes.application.ports import (
    NodeCommentBanDTO,
    NodeCommentDTO,
    NodeCommentsRepo,
    NodeReactionsRepo,
    NodeReactionsSummary,
    NodeViewsRepo,
    NodeViewStat,
)

_DEFAULT_REACTION = "like"


class NodeViewsService:
    def __init__(
        self, repo: NodeViewsRepo, *, clock: Callable[[], datetime] | None = None
    ) -> None:
        self.repo = repo
        self._clock = clock or (lambda: datetime.now(UTC))

    async def register_view(
        self,
        node_id: int,
        *,
        viewer_id: str | None = None,
        fingerprint: str | None = None,
        amount: int = 1,
        at: datetime | None = None,
    ) -> int:
        if amount <= 0:
            raise ValueError("amount_positive_required")
        when = at or self._clock()
        return await self.repo.increment(
            node_id,
            amount=amount,
            viewer_id=viewer_id,
            fingerprint=fingerprint,
            at=when.replace(microsecond=0).isoformat(),
        )

    async def get_total(self, node_id: int) -> int:
        return await self.repo.get_total(node_id)

    async def get_daily(
        self, node_id: int, *, limit: int = 30, offset: int = 0
    ) -> list[NodeViewStat]:
        return await self.repo.get_daily(node_id, limit=limit, offset=offset)


class NodeReactionsService:
    def __init__(self, repo: NodeReactionsRepo) -> None:
        self.repo = repo

    async def add_like(self, node_id: int, user_id: str) -> bool:
        return await self.repo.add(node_id, user_id, _DEFAULT_REACTION)

    async def remove_like(self, node_id: int, user_id: str) -> bool:
        return await self.repo.remove(node_id, user_id, _DEFAULT_REACTION)

    async def toggle_like(self, node_id: int, user_id: str) -> bool:
        has_reaction = await self.repo.has(node_id, user_id, _DEFAULT_REACTION)
        if has_reaction:
            await self.repo.remove(node_id, user_id, _DEFAULT_REACTION)
            return False
        await self.repo.add(node_id, user_id, _DEFAULT_REACTION)
        return True

    async def get_summary(
        self, node_id: int, *, user_id: str | None = None
    ) -> NodeReactionsSummary:
        totals = await self.repo.counts(node_id)
        user_reaction: str | None = None
        if user_id:
            if await self.repo.has(node_id, user_id, _DEFAULT_REACTION):
                user_reaction = _DEFAULT_REACTION
        return NodeReactionsSummary(
            node_id=node_id, totals=totals, user_reaction=user_reaction
        )


class NodeCommentsService:
    def __init__(
        self,
        repo: NodeCommentsRepo,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.repo = repo
        self._clock = clock or (lambda: datetime.now(UTC))

    async def create_comment(
        self,
        *,
        node_id: int,
        author_id: str,
        content: str,
        parent_comment_id: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> NodeCommentDTO:
        normalized = (content or "").strip()
        if not normalized:
            raise ValueError("content_required")
        payload = dict(metadata) if metadata else {}
        return await self.repo.create(
            node_id=node_id,
            author_id=author_id,
            content=normalized,
            parent_comment_id=parent_comment_id,
            metadata=payload,
        )

    async def get_comment(self, comment_id: int) -> NodeCommentDTO | None:
        return await self.repo.get(comment_id)

    async def list_comments(
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

    async def delete_comment(
        self,
        comment_id: int,
        *,
        actor_id: str,
        hard: bool = False,
        reason: str | None = None,
    ) -> bool:
        if hard:
            return await self.repo.hard_delete(comment_id)
        return await self.repo.soft_delete(comment_id, actor_id=actor_id, reason=reason)

    async def update_status(
        self,
        comment_id: int,
        *,
        status: str,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> NodeCommentDTO:
        normalized = status.strip().lower()
        if not normalized:
            raise ValueError("status_required")
        return await self.repo.update_status(
            comment_id,
            normalized,
            actor_id=actor_id,
            reason=reason,
        )

    async def lock_comments(
        self,
        node_id: int,
        *,
        actor_id: str,
        reason: str | None = None,
    ) -> None:
        locked_at = self._clock().replace(microsecond=0).isoformat()
        await self.repo.lock_node(
            node_id,
            locked_by=actor_id,
            locked_at=locked_at,
            reason=reason,
        )

    async def unlock_comments(
        self, node_id: int, *, actor_id: str | None = None
    ) -> None:
        await self.repo.lock_node(
            node_id,
            locked_by=None,
            locked_at=None,
            reason=None,
        )

    async def disable_comments(
        self,
        node_id: int,
        *,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> None:
        await self.repo.set_comments_disabled(
            node_id,
            disabled=True,
            actor_id=actor_id,
            reason=reason,
        )

    async def enable_comments(
        self,
        node_id: int,
        *,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> None:
        await self.repo.set_comments_disabled(
            node_id,
            disabled=False,
            actor_id=actor_id,
            reason=reason,
        )

    async def ban_user(
        self,
        node_id: int,
        target_user_id: str,
        *,
        actor_id: str,
        reason: str | None = None,
    ) -> NodeCommentBanDTO:
        return await self.repo.record_ban(
            node_id,
            target_user_id,
            set_by=actor_id,
            reason=reason,
        )

    async def unban_user(self, node_id: int, target_user_id: str) -> bool:
        return await self.repo.remove_ban(node_id, target_user_id)

    async def is_user_banned(self, node_id: int, target_user_id: str) -> bool:
        return await self.repo.is_banned(node_id, target_user_id)

    async def list_bans(self, node_id: int) -> list[NodeCommentBanDTO]:
        return await self.repo.list_bans(node_id)
