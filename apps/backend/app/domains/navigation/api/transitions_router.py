from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.db.session import get_db
from app.core.workspace_context import require_workspace
from app.domains.navigation.application.navigation_cache_service import (
    NavigationCacheService,
)
from app.domains.navigation.infrastructure.cache_adapter import CoreCacheAdapter
from app.domains.navigation.policies.transition_policy import TransitionPolicy
from app.domains.nodes.infrastructure.repositories.node_repository import (
    NodeRepositoryAdapter,
)
from app.domains.users.infrastructure.models.user import User
from app.domains.navigation.infrastructure.repositories.transition_repository import (
    TransitionRepository,
)

router = APIRouter(prefix="/transitions", tags=["transitions"])
navcache = NavigationCacheService(CoreCacheAdapter())


@router.delete("/{transition_id}", summary="Delete transition")
async def delete_transition(
    transition_id: str,
    workspace_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    _workspace: Annotated[object, Depends(require_workspace)] = ...,
):
    """Delete a specific manual transition between nodes."""
    repo = TransitionRepository(db)
    node_repo = NodeRepositoryAdapter(db)
    transition = await repo.get(transition_id)
    if not transition:
        raise HTTPException(status_code=404, detail="Transition not found")
    TransitionPolicy.ensure_can_delete(transition, current_user)
    from_node = await node_repo.get_by_alt_id(transition.from_node_id, workspace_id)
    await repo.delete(transition)
    if from_node:
        await navcache.invalidate_navigation_by_node(from_node.slug)
    return {"message": "Transition deleted"}
