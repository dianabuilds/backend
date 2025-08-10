from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import assert_owner_or_role, get_current_user
from app.db.session import get_db
from app.models.transition import NodeTransition
from app.models.user import User

router = APIRouter(prefix="/transitions", tags=["transitions"])


@router.delete("/{transition_id}")
async def delete_transition(
    transition_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    transition = await db.get(NodeTransition, transition_id)
    if not transition:
        raise HTTPException(status_code=404, detail="Transition not found")
    assert_owner_or_role(transition.created_by, "moderator", current_user)
    await db.delete(transition)
    await db.commit()
    return {"message": "Transition deleted"}
