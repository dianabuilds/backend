from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserPremiumUpdate, UserRoleUpdate

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/users/{user_id}/premium")
async def set_user_premium(
    user_id: UUID,
    payload: UserPremiumUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_premium = payload.is_premium
    user.premium_until = payload.premium_until
    await db.commit()
    await db.refresh(user)
    return {"is_premium": user.is_premium, "premium_until": user.premium_until}


@router.post("/users/{user_id}/role")
async def set_user_role(
    user_id: UUID,
    payload: UserRoleUpdate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = payload.role
    await db.commit()
    await db.refresh(user)
    return {"role": user.role}
