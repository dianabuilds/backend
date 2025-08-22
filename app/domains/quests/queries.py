from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.domains.quests.infrastructure.models.quest_models import Quest
from app.domains.users.infrastructure.models.user import User
from app.domains.quests.access import can_view


async def list_public(db: AsyncSession) -> List[Quest]:
    res = await db.execute(
        select(Quest).where(Quest.is_draft == False, Quest.is_deleted == False).order_by(Quest.published_at.desc())  # noqa: E712
    )
    return list(res.scalars().all())


async def search(
    db: AsyncSession,
    *,
    q: str | None,
    tags: list[str] | None,
    author_id,
    free_only: bool,
    premium_only: bool,
    sort_by: str,
    page: int,
    per_page: int,
) -> List[Quest]:
    stmt = select(Quest).where(Quest.is_draft == False, Quest.is_deleted == False)  # noqa: E712

    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                Quest.title.ilike(pattern),
                Quest.subtitle.ilike(pattern),
                Quest.description.ilike(pattern),
            )
        )

    if tags:
        for tag in tags:
            stmt = stmt.where(Quest.tags.like(f'%"{tag}"%'))

    if author_id:
        stmt = stmt.where(Quest.author_id == author_id)

    if free_only:
        stmt = stmt.where(or_(Quest.price == None, Quest.price == 0))  # noqa: E711

    if premium_only:
        stmt = stmt.where(Quest.is_premium_only == True)  # noqa: E712

    if sort_by == "price":
        stmt = stmt.order_by(Quest.price.asc())
    elif sort_by == "title":
        stmt = stmt.order_by(Quest.title.asc())
    elif sort_by == "popularity":
        stmt = stmt.order_by(func.coalesce(Quest.published_at, datetime.min).desc())
    else:
        stmt = stmt.order_by(Quest.published_at.desc())

    offset = (page - 1) * per_page
    stmt = stmt.offset(offset).limit(per_page)

    res = await db.execute(stmt)
    return list(res.scalars().all())


async def get_for_view(db: AsyncSession, *, slug: str, user: User) -> Quest:
    res = await db.execute(select(Quest).where(Quest.slug == slug, Quest.is_deleted == False))  # noqa: E712
    quest = res.scalars().first()
    if not quest or (quest.is_draft and quest.author_id != user.id):
        raise ValueError("Quest not found")
    if not await can_view(db, quest=quest, user=user):
        raise PermissionError("No access")
    return quest
