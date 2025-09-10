from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.domains.navigation.application.navigation_cache_service import (
    NavigationCacheService,
)
from app.domains.navigation.infrastructure.cache_adapter import CoreCacheAdapter
from app.domains.navigation.infrastructure.repositories.transition_repository import (
    TransitionRepository,
)
from app.domains.navigation.policies.transition_policy import TransitionPolicy
from app.domains.nodes.infrastructure.repositories.node_repository import (
    NodeRepository,
)
from app.domains.users.infrastructure.models.user import User
from app.providers.db.session import get_db

router = APIRouter(prefix="/transitions", tags=["transitions"])
navcache = NavigationCacheService(CoreCacheAdapter())


@router.delete("/{transition_id}", summary="Delete transition")
async def delete_transition(
    transition_id: str,
    workspace_id: Annotated[int | None, Query()] = None,
    tenant_id: Annotated[int | None, Query()] = None,
    current_user: Annotated[User, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
    # Profile-centric: no membership dependency
):
    """Delete a specific manual transition between nodes."""
    repo = TransitionRepository(db)
    node_repo = NodeRepository(db)
    transition = await repo.get(transition_id)
    if not transition:
        raise HTTPException(status_code=404, detail="Transition not found")
    TransitionPolicy.ensure_can_delete(transition, current_user)
    account_scope = tenant_id or workspace_id
    if account_scope is None:
        raise HTTPException(status_code=422, detail="tenant_id is required")
    from_node = await node_repo.get_by_id(transition.from_node_id, account_scope)
    await repo.delete(transition)
    if from_node:
        await navcache.invalidate_navigation_by_node(
            account_id=account_scope, node_slug=from_node.slug
        )
    return {"message": "Transition deleted"}
