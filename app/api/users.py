from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserOut)
async def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ):
    data = payload.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(current_user, field, value)
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.delete("/me")
async def delete_me(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    current_user.is_active = False
    current_user.deleted_at = datetime.utcnow()
    current_user.email = None
    current_user.password_hash = None
    current_user.username = None
    current_user.bio = None
    current_user.avatar_url = None
    current_user.is_premium = False
    current_user.premium_until = None
    await db.commit()
    return {"message": "Account deleted"}
