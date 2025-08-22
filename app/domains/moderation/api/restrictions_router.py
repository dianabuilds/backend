from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import assert_seniority_over
from app.core.db.session import get_db
from app.domains.moderation.infrastructure.models.moderation_models import UserRestriction
from app.domains.users.infrastructure.models.user import User
from app.schemas.moderation import (
    RestrictionOut,
    RestrictionAdminCreate,
    RestrictionAdminUpdate,
)
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

admin_required = require_admin_role()

router = APIRouter(
    prefix="/admin/restrictions",
    tags=["admin"],
    dependencies=[Depends(admin_required)],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.get("", response_model=list[RestrictionOut])
async def list_restrictions(
    user_id: UUID | None = None,
    type: str | None = None,
    page: int = 1,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(UserRestriction).order_by(UserRestriction.created_at.desc())
    if user_id:
        stmt = stmt.where(UserRestriction.user_id == user_id)
    if type:
        stmt = stmt.where(UserRestriction.type == type)
    page_size = 50
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("", response_model=RestrictionOut)
async def create_restriction(
    payload: RestrictionAdminCreate,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    target_user = await db.get(User, payload.user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    assert_seniority_over(target_user, current_user)
    if (
        payload.type == "ban"
        and payload.expires_at is None
        and current_user.role != "admin"
    ):
        raise HTTPException(status_code=403, detail="Permanent ban requires admin")
    now = datetime.utcnow()
    res = await db.execute(
        select(UserRestriction).where(
            UserRestriction.user_id == payload.user_id,
            UserRestriction.type == payload.type,
            ((UserRestriction.expires_at == None) | (UserRestriction.expires_at > now)),
        )
    )
    if res.scalars().first():
        raise HTTPException(status_code=409, detail="Active restriction exists")
    restriction = UserRestriction(
        user_id=payload.user_id,
        type=payload.type,
        reason=payload.reason,
        expires_at=payload.expires_at,
        issued_by=current_user.id,
    )
    db.add(restriction)
    await db.commit()
    await db.refresh(restriction)
    return restriction


@router.patch("/{restriction_id}", response_model=RestrictionOut)
async def update_restriction(
    restriction_id: UUID,
    payload: RestrictionAdminUpdate,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    restriction = await db.get(UserRestriction, restriction_id)
    if not restriction:
        raise HTTPException(status_code=404, detail="Restriction not found")
    target_user = await db.get(User, restriction.user_id)
    if target_user:
        assert_seniority_over(target_user, current_user)
    if payload.reason is not None:
        restriction.reason = payload.reason
    if payload.expires_at is not None:
        restriction.expires_at = payload.expires_at
    await db.commit()
    await db.refresh(restriction)
    return restriction


@router.delete("/{restriction_id}")
async def delete_restriction(
    restriction_id: UUID,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    restriction = await db.get(UserRestriction, restriction_id)
    if not restriction:
        raise HTTPException(status_code=404, detail="Restriction not found")
    target_user = await db.get(User, restriction.user_id)
    if target_user:
        assert_seniority_over(target_user, current_user)
    await db.delete(restriction)
    await db.commit()
    return {"status": "ok"}
