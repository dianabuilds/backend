from __future__ import annotations

from dataclasses import dataclass

from domains.product.nodes.application.ports import (
    NodeReactionsRepo,
    NodeReactionsSummary,
    NodeViewsRepo,
    NodeViewStat,
)


@dataclass
class EngagementRepository:
    views_repo: NodeViewsRepo
    reactions_repo: NodeReactionsRepo | None = None

    async def increment_view(
        self,
        node_id: int,
        *,
        amount: int = 1,
        viewer_id: str | None = None,
        fingerprint: str | None = None,
        at: str | None = None,
    ) -> int:
        return await self.views_repo.increment(
            node_id,
            amount=amount,
            viewer_id=viewer_id,
            fingerprint=fingerprint,
            at=at,
        )

    async def get_total_views(self, node_id: int) -> int:
        return await self.views_repo.get_total(node_id)

    async def get_view_stats(
        self, node_id: int, *, limit: int = 30, offset: int = 0
    ) -> list[NodeViewStat]:
        return await self.views_repo.get_daily(node_id, limit=limit, offset=offset)

    async def add_like(
        self, node_id: int, *, user_id: str, reaction_type: str = "like"
    ) -> bool:
        if self.reactions_repo is None:
            raise RuntimeError("node_reactions_repo_not_configured")
        return await self.reactions_repo.add(node_id, user_id, reaction_type)

    async def remove_like(
        self, node_id: int, *, user_id: str, reaction_type: str = "like"
    ) -> bool:
        if self.reactions_repo is None:
            raise RuntimeError("node_reactions_repo_not_configured")
        return await self.reactions_repo.remove(node_id, user_id, reaction_type)

    async def get_reactions_summary(
        self, node_id: int, *, user_id: str | None = None
    ) -> NodeReactionsSummary:
        if self.reactions_repo is None:
            raise RuntimeError("node_reactions_repo_not_configured")
        totals = await self.reactions_repo.counts(node_id)
        user_reaction: str | None = None
        if user_id:
            has = await self.reactions_repo.has(node_id, user_id, "like")
            user_reaction = "like" if has else None
        return NodeReactionsSummary(
            node_id=node_id,
            totals=totals,
            user_reaction=user_reaction,
        )

    async def list_reactions(self, node_id: int, *, limit: int = 100, offset: int = 0):
        if self.reactions_repo is None:
            raise RuntimeError("node_reactions_repo_not_configured")
        return await self.reactions_repo.list_for_node(
            node_id, limit=limit, offset=offset
        )
