from __future__ import annotations

from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import String, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.domains.moderation.infrastructure.models.moderation_models import UserRestriction
from app.domains.users.infrastructure.models.user import User
from app.schemas.user import AdminUserOut, UserPremiumUpdate, UserRoleUpdate
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role
from app.api.deps import assert_seniority_over

router = APIRouter(prefix="/admin/users", tags=["admin"], responses=ADMIN_AUTH_RESPONSES)
admin_only = require_admin_role({"admin"})
admin_required = require_admin_role()


@router.get("", response_model=List[AdminUserOut], summary="List users")
async def list_users(
    q: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
    premium: str | None = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User).offset(offset).limit(limit)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                User.email.ilike(pattern),
                User.username.ilike(pattern),
                func.cast(User.id, String).ilike(pattern),
            )
        )
    if role:
        stmt = stmt.where(User.role == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    if premium == "active":
        stmt = stmt.where(User.is_premium == True)  # noqa: E712
    elif premium == "expired":
        stmt = stmt.where(User.is_premium == False)  # noqa: E712

    result = await db.execute(stmt)
    users = result.scalars().all()

    user_ids = [u.id for u in users]
    restrictions_map: dict[UUID, list[UserRestriction]] = {}
    if user_ids:
        res = await db.execute(
            select(UserRestriction).where(UserRestriction.user_id.in_(user_ids))
        )
        for r in res.scalars().all():
            restrictions_map.setdefault(r.user_id, []).append(r)

    return [
        AdminUserOut(
            id=u.id,
            created_at=u.created_at,
            email=u.email,
            wallet_address=u.wallet_address,
            is_active=u.is_active,
            username=u.username,
            bio=u.bio,
            avatar_url=u.avatar_url,
            role=u.role,
            is_premium=u.is_premium,
            premium_until=u.premium_until,
            restrictions=restrictions_map.get(u.id, []),
        )
        for u in users
    ]


@router.post("/{user_id}/premium", summary="Set user premium status")
async def set_user_premium(
    user_id: UUID,
    payload: UserPremiumUpdate,
    current_user: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
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
    return {"is_premium": user.is_premium, "premium_until": user.premium_until}


@router.post("/{user_id}/role", summary="Change user role")
async def set_user_role(
    user_id: UUID,
    payload: UserRoleUpdate,
    current_user: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if current_user.id == user.id:
        raise HTTPException(status_code=403, detail="Cannot modify self")
    assert_seniority_over(user, current_user)
    user.role = payload.role
    await db.commit()
    await db.refresh(user)
    return {"role": user.role}
