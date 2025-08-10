from datetime import datetime
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.deps import assert_seniority_over, require_role
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserPremiumUpdate, UserRoleUpdate

router = APIRouter(prefix="/admin", tags=["admin"])

logger = logging.getLogger(__name__)


@router.post("/users/{user_id}/premium", summary="Set user premium status")
async def set_user_premium(
    user_id: UUID,
    payload: UserPremiumUpdate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Grant or revoke premium access for a specific user."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if current_user.id == user.id:
        raise HTTPException(status_code=403, detail="Cannot modify self")
    assert_seniority_over(user, current_user)
    user.is_premium = payload.is_premium
    user.premium_until = payload.premium_until
    await db.commit()
    await db.refresh(user)
    logger.info(
        "admin_action",
        extra={
            "action": "set_premium",
            "actor_id": str(current_user.id),
            "target_user_id": str(user.id),
            "payload": payload.model_dump(),
            "ts": datetime.utcnow().isoformat(),
        },
    )
    return {"is_premium": user.is_premium, "premium_until": user.premium_until}


@router.post("/users/{user_id}/role", summary="Change user role")
async def set_user_role(
    user_id: UUID,
    payload: UserRoleUpdate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Assign a new role to a user."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if current_user.id == user.id:
        raise HTTPException(status_code=403, detail="Cannot modify self")
    assert_seniority_over(user, current_user)
    user.role = payload.role
    await db.commit()
    await db.refresh(user)
    logger.info(
        "admin_action",
        extra={
            "action": "set_role",
            "actor_id": str(current_user.id),
            "target_user_id": str(user.id),
            "payload": payload.model_dump(),
            "ts": datetime.utcnow().isoformat(),
        },
    )
    return {"role": user.role}
