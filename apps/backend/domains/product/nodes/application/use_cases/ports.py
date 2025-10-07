from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from domains.product.nodes.application.ports import (
    NodeCommentBanDTO,
    NodeCommentDTO,
    NodeReactionsSummary,
    NodeViewStat,
)
from domains.product.nodes.domain.results import NodeView


class NodesServicePort(Protocol):
    async def update_tags(
        self, node_id: int, new_slugs: Sequence[str], *, actor_id: str
    ) -> NodeView: ...

    async def create(
        self,
        *,
        author_id: str,
        title: str | None,
        tags: Sequence[str] | None,
        is_public: bool,
        status: str | None = None,
        publish_at: str | None = None,
        unpublish_at: str | None = None,
        content_html: str | None = None,
        cover_url: str | None = None,
    ) -> NodeView: ...

    async def update(
        self,
        node_id: int,
        *,
        title: str | None = None,
        is_public: bool | None = None,
        status: str | None = None,
        publish_at: str | None = None,
        unpublish_at: str | None = None,
        content_html: str | None = None,
        cover_url: str | None = None,
    ) -> NodeView: ...

    async def delete(self, node_id: int) -> bool: ...

    async def register_view(
        self,
        node_id: int,
        *,
        viewer_id: str | None = None,
        fingerprint: str | None = None,
        amount: int = 1,
        at: datetime | None = None,
    ) -> int: ...

    async def get_total_views(self, node_id: int) -> int: ...

    async def get_view_stats(
        self, node_id: int, *, limit: int = 30, offset: int = 0
    ) -> list[NodeViewStat]: ...

    async def add_like(self, node_id: int, *, user_id: str) -> bool: ...

    async def remove_like(self, node_id: int, *, user_id: str) -> bool: ...

    async def get_reactions_summary(
        self, node_id: int, *, user_id: str | None = None
    ) -> NodeReactionsSummary: ...

    async def list_comments(
        self,
        node_id: int,
        *,
        parent_comment_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> list[NodeCommentDTO]: ...

    async def create_comment(
        self,
        *,
        node_id: int,
        author_id: str,
        content: str,
        parent_comment_id: int | None = None,
        metadata: dict | None = None,
    ) -> NodeCommentDTO: ...

    async def get_comment(self, comment_id: int) -> NodeCommentDTO | None: ...

    async def delete_comment(
        self,
        comment_id: int,
        *,
        actor_id: str,
        hard: bool = False,
        reason: str | None = None,
    ) -> bool: ...

    async def update_comment_status(
        self,
        comment_id: int,
        *,
        status: str,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> NodeCommentDTO: ...

    async def lock_comments(
        self, node_id: int, *, actor_id: str, reason: str | None = None
    ) -> None: ...

    async def unlock_comments(
        self, node_id: int, *, actor_id: str | None = None
    ) -> None: ...

    async def disable_comments(
        self,
        node_id: int,
        *,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> None: ...

    async def enable_comments(
        self,
        node_id: int,
        *,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> None: ...

    async def ban_comment_user(
        self,
        node_id: int,
        target_user_id: str,
        *,
        actor_id: str,
        reason: str | None = None,
    ) -> NodeCommentBanDTO: ...

    async def unban_comment_user(self, node_id: int, target_user_id: str) -> bool: ...

    async def list_comment_bans(self, node_id: int) -> list[NodeCommentBanDTO]: ...

    async def _repo_get_async(self, node_id: int): ...

    async def _repo_get_by_slug_async(self, slug: str): ...

    def _to_view(self, dto): ...
