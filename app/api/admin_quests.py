from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, func
from uuid import UUID

from app.db.session import get_db
from app.models.quest import Quest
from app.models.user import User
from app.schemas.quest import QuestOut
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

admin_required = require_admin_role({"admin", "moderator"})

router = APIRouter(
    prefix="/admin/quests",
    tags=["admin"],
    dependencies=[Depends(admin_required)],
    responses=ADMIN_AUTH_RESPONSES,
)


@router.get("", response_model=list[QuestOut], summary="Admin list quests with filters")
async def admin_list_quests(
    q: Optional[str] = None,
    author_role: Optional[str] = Query(None, pattern="^(admin|moderator|user)$"),
    author_id: Optional[UUID] = None,
    draft: Optional[bool] = None,
    deleted: Optional[bool] = None,
    free_only: bool = False,
    premium_only: bool = False,
    sort_by: str = Query("new", pattern="^(new|price|title|popularity)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Quest)
    # фильтрация статуса
    if draft is not None:
        stmt = stmt.where(Quest.is_draft.is_(draft))
    if deleted is not None:
        stmt = stmt.where(Quest.is_deleted.is_(deleted))
    # текстовый поиск
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                Quest.title.ilike(pattern),
                Quest.subtitle.ilike(pattern),
                Quest.description.ilike(pattern),
            )
        )
    # фильтры стоимости/премиума
    if free_only:
        stmt = stmt.where(or_(Quest.price == None, Quest.price == 0))  # noqa: E711
    if premium_only:
        stmt = stmt.where(Quest.is_premium_only.is_(True))
    # автор: по id или по роли
    if author_id:
        stmt = stmt.where(Quest.author_id == author_id)
    elif author_role:
        stmt = stmt.join(User, User.id == Quest.author_id).where(User.role == author_role)

    # сортировка
    if sort_by == "price":
        stmt = stmt.order_by(Quest.price.asc().nullsLast())
    elif sort_by == "title":
        stmt = stmt.order_by(Quest.title.asc())
    elif sort_by == "popularity":
        stmt = stmt.order_by(func.coalesce(Quest.published_at, datetime.min).desc())
    else:  # new
        stmt = stmt.order_by(Quest.created_at.desc())

    # пагинация
    offset = (page - 1) * per_page
    stmt = stmt.offset(offset).limit(per_page)

    result = await db.execute(stmt)
    return result.scalars().all()
