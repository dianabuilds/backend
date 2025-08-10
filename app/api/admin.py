from datetime import datetime
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, String
from uuid import UUID

from app.api.deps import assert_seniority_over, require_role
from app.db.session import get_db
from app.models.user import User
from app.models.moderation import UserRestriction
from app.schemas.user import UserPremiumUpdate, UserRoleUpdate, AdminUserOut

router = APIRouter(prefix="/admin", tags=["admin"])

logger = logging.getLogger(__name__)


@router.get("/users", response_model=list[AdminUserOut], summary="List users")
async def list_users(
    q: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
    premium: str | None = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(require_role("moderator")),
    db: AsyncSession = Depends(get_db),
):
    """Return a paginated list of users with optional filters."""
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
