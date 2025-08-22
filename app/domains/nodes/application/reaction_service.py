from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.application.ports.node_repo_port import INodeRepository
from app.domains.navigation.application.navigation_cache_service import NavigationCacheService
from app.core.log_events import cache_invalidate
from app.domains.audit.application.audit_service import audit_log


_ALLOWED_REACTIONS = {"like", "love", "wow", "sad", "angry"}
_ALLOWED_ACTIONS = {"add", "remove"}


class ReactionService:
    def __init__(self, repo: INodeRepository, navcache: NavigationCacheService) -> None:
        self._repo = repo
        self._navcache = navcache

    async def update_reactions_by_slug(
        self,
        db: AsyncSession,
        slug: str,
        reaction: str,
        action: str,
        *,
        actor_id: str | None = None,
    ) -> dict:
        if reaction not in _ALLOWED_REACTIONS:
            raise HTTPException(status_code=400, detail="Invalid reaction")
        if action not in _ALLOWED_ACTIONS:
            raise HTTPException(status_code=400, detail="Invalid action")

        node = await self._repo.get_by_slug(slug)
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")

        node = await self._repo.update_reactions(node, reaction, action)

        # Инвалидация компаса (влияние на рекомендации)
        await self._navcache.invalidate_compass_all()
        cache_invalidate("comp", reason="reaction_update", key=slug)

        # Аудит
        try:
            if actor_id:
                await audit_log(
                    db,
                    actor_id=actor_id,
                    action="node_reaction_update",
                    resource_type="node",
                    resource_id=str(node.id),
                    extra={"reaction": reaction, "action": action},
                )
        except Exception:
            # аудит best-effort
            pass

        return {"reactions": node.reactions}
