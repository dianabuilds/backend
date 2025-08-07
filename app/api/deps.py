from datetime import datetime
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import verify_access_token
from app.db.session import get_db
from app.models.user import User
from app.models.moderation import UserRestriction

# Обновляем URL для получения токена, указывая, что используется username+password
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    user_id_str = verify_access_token(token)
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = await db.get(User, user_id)
    if not user or not user.is_active or user.deleted_at is not None:
        raise HTTPException(status_code=404, detail="User not found")
    result = await db.execute(
        select(UserRestriction).where(
            UserRestriction.user_id == user.id,
            UserRestriction.type == "ban",
            (UserRestriction.expires_at == None) | (UserRestriction.expires_at > datetime.utcnow()),
        )
    )
    if result.scalars().first():
        raise HTTPException(status_code=403, detail="User is banned")
    return user


async def require_premium(user: User = Depends(get_current_user)) -> User:
    if not user.is_premium or (
        user.premium_until and user.premium_until < datetime.utcnow()
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required",
        )
    return user


role_order = {"user": 0, "moderator": 1, "admin": 2}


def require_role(min_role: str = "moderator"):
    async def _require_role(user: User = Depends(get_current_user)) -> User:
        if role_order.get(user.role, 0) < role_order[min_role]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return _require_role


async def ensure_can_post(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    result = await db.execute(
        select(UserRestriction).where(
            UserRestriction.user_id == user.id,
            UserRestriction.type == "post_restrict",
            (UserRestriction.expires_at == None) | (UserRestriction.expires_at > datetime.utcnow()),
        )
    )
    if result.scalars().first():
        raise HTTPException(status_code=403, detail="Posting restricted")
    return user
