from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.deps import get_current_user, get_db
from app.core.workspace_context import require_workspace
from app.domains.navigation.application.echo_service import EchoService
from app.domains.navigation.application.navigation_cache_service import NavigationCacheService
from app.domains.navigation.infrastructure.cache_adapter import CoreCacheAdapter
from app.domains.users.infrastructure.models.user import User
from app.domains.nodes.infrastructure.repositories.node_repository import (
    NodeRepositoryAdapter,
)
from app.domains.navigation.infrastructure.repositories.transition_repository import (
    TransitionRepository,
)
from app.domains.nodes.policies.node_policy import NodePolicy
from app.schemas.transition import NodeTransitionCreate
from app.core.log_events import cache_invalidate

router = APIRouter(prefix="/nodes", tags=["nodes-navigation-manage"])
navcache = NavigationCacheService(CoreCacheAdapter())


@router.post(
    "/{slug}/visit/{to_slug}",
    response_model=dict,
    summary="Record visit",
)
async def record_visit(
    slug: str,
    to_slug: str,
    workspace_id: UUID,
    source: str | None = None,
    channel: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _workspace: object = Depends(require_workspace),
):
    repo = NodeRepositoryAdapter(db)
    from_node = await repo.get_by_slug(slug, workspace_id)
    if not from_node:
        raise HTTPException(status_code=404, detail="Node not found")
    to_node = await repo.get_by_slug(to_slug, workspace_id)
    if not to_node:
        raise HTTPException(status_code=404, detail="Target node not found")
    await EchoService().record_echo_trace(db, from_node, to_node, current_user, source=source, channel=channel)
    return {"status": "ok"}


@router.post(
    "/{slug}/transitions",
    response_model=dict,
    summary="Create transition",
)
async def create_transition(
    slug: str,
    payload: NodeTransitionCreate,
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _workspace: object = Depends(require_workspace),
):
    repo = NodeRepositoryAdapter(db)
    from_node = await repo.get_by_slug(slug, workspace_id)
    if not from_node:
        raise HTTPException(status_code=404, detail="Node not found")
    NodePolicy.ensure_can_edit(from_node, current_user)
    to_node = await repo.get_by_slug(payload.to_slug, workspace_id)
    if not to_node:
        raise HTTPException(status_code=404, detail="Target node not found")
    t_repo = TransitionRepository(db)
    transition = await t_repo.create(from_node.id, to_node.id, payload, current_user.id)
    await navcache.invalidate_navigation_by_node(slug)
    cache_invalidate("nav", reason="transition_create", key=slug)
    return {"id": str(transition.id)}
