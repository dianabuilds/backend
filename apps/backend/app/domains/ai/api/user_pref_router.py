from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.infrastructure.repositories.user_pref_repository import (
    UserAIPrefRepository,
)
from app.domains.ai.schemas.user_pref import UserAIPrefIn, UserAIPrefOut
from app.domains.users.infrastructure.models.user import User
from app.kernel.db import get_db
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

admin_required = require_admin_role({"admin", "moderator"})

router = APIRouter(
    prefix="/admin/ai",
    tags=["admin-ai-user-pref"],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.get("/user-pref", response_model=UserAIPrefOut)
async def get_user_pref(
    current: Annotated[User, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> UserAIPrefOut:
    repo = UserAIPrefRepository(db)
    pref = await repo.get(current.id)
    return UserAIPrefOut(model=pref.model if pref else None)


@router.put("/user-pref", response_model=UserAIPrefOut)
async def put_user_pref(
    body: UserAIPrefIn,
    current: Annotated[User, Depends(admin_required)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> UserAIPrefOut:
    repo = UserAIPrefRepository(db)
    pref = await repo.set(current.id, body.model)
    await db.commit()
    return UserAIPrefOut(model=pref.model)

