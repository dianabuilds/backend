from datetime import datetime
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import load_only

from app.core.security import verify_access_token
from app.db.session import get_db
from app.models.user import User
from app.models.moderation import UserRestriction
from app.core.log_filters import user_id_var

# Обновляем URL для получения токена, указывая, что используется username+password
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
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
    # Выбираем только безопасные колонки, чтобы не падать на отсутствующих (например, premium_until)
    result = await db.execute(
        select(User)
        .options(
            load_only(
                User.id,
                User.created_at,
                User.email,
                User.password_hash,
                User.wallet_address,
                User.is_active,
                User.username,
                User.bio,
                User.avatar_url,
                User.role,
                User.deleted_at,
            )
        )
        .where(User.id == user_id)
    )
    user = result.scalars().first()
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
    request.state.user_id = str(user.id)
    user_id_var.set(str(user.id))
    return user


async def get_current_user_optional(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User | None:
    """Return current user if Authorization header present, otherwise None."""
    auth = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return None
    token = auth.split(" ", 1)[1]
    user_id_str = verify_access_token(token)
    if not user_id_str:
        return None
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        return None
    user = await db.get(User, user_id)
    if not user or not user.is_active or user.deleted_at is not None:
        return None
    result = await db.execute(
        select(UserRestriction).where(
            UserRestriction.user_id == user.id,
            UserRestriction.type == "ban",
            (UserRestriction.expires_at == None)
            | (UserRestriction.expires_at > datetime.utcnow()),
        )
    )
    if result.scalars().first():
        return None
    request.state.user_id = str(user.id)
    user_id_var.set(str(user.id))
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


"""Common authorization helpers and role hierarchy for API dependencies.

Roles have strict seniority: ``user < moderator < admin``.  Helpers below
leverage this ranking to provide unified access checks across the API.
"""

role_order = {"user": 0, "moderator": 1, "admin": 2}


def require_role(min_role: str = "moderator"):
    async def _require_role(user: User = Depends(get_current_user)) -> User:
        if role_order.get(user.role, 0) < role_order[min_role]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return _require_role


def assert_owner_or_role(owner_id: UUID, min_role: str, current_user: User) -> None:
    """Allow action if ``current_user`` owns the entity or has ``min_role``.

    Args:
        owner_id: Identifier of the entity owner.
        min_role: Minimal role required when user is not the owner.
        current_user: Authenticated user performing the action.
    """
    if current_user.id != owner_id and role_order.get(current_user.role, 0) < role_order[
        min_role
    ]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")


def assert_seniority_over(target_user: User, current_user: User) -> None:
    """Ensure ``current_user`` is strictly senior to ``target_user``.

    Raises ``HTTPException`` with status 403 if the check fails.
    """
    if role_order.get(current_user.role, 0) <= role_order.get(target_user.role, 0):
        raise HTTPException(status_code=403, detail="Insufficient permissions")


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
