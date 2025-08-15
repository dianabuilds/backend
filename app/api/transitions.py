from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.policies import TransitionPolicy
from app.repositories import NodeRepository, TransitionRepository
from app.services.navcache import navcache

router = APIRouter(prefix="/transitions", tags=["transitions"])


@router.delete("/{transition_id}", summary="Delete transition")
async def delete_transition(
    transition_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a specific manual transition between nodes."""
    repo = TransitionRepository(db)
    node_repo = NodeRepository(db)
    transition = await repo.get(transition_id)
    if not transition:
        raise HTTPException(status_code=404, detail="Transition not found")
    TransitionPolicy.ensure_can_delete(transition, current_user)
    from_node = await node_repo.get_by_id(transition.from_node_id)
    await repo.delete(transition)
    if from_node:
        await navcache.invalidate_navigation_by_node(from_node.slug)
    return {"message": "Transition deleted"}
