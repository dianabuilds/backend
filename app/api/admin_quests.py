from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, func
from uuid import UUID

from app.db.session import get_db
from app.models.quest import Quest
from app.models.user import User
from app.schemas.quest import QuestOut, QuestUpdate
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role
from app.services.audit import audit_log

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
    if draft is not None:
        stmt = stmt.where(Quest.is_draft.is_(draft))
    if deleted is not None:
        stmt = stmt.where(Quest.is_deleted.is_(deleted))
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                Quest.title.ilike(pattern),
                Quest.subtitle.ilike(pattern),
                Quest.description.ilike(pattern),
            )
        )
    if free_only:
        stmt = stmt.where(or_(Quest.price == None, Quest.price == 0))  # noqa: E711
    if premium_only:
        stmt = stmt.where(Quest.is_premium_only.is_(True))
    if author_id:
        stmt = stmt.where(Quest.author_id == author_id)
    elif author_role:
        stmt = stmt.join(User, User.id == Quest.author_id).where(User.role == author_role)

    if sort_by == "price":
        stmt = stmt.order_by(Quest.price.asc().nullsLast())
    elif sort_by == "title":
        stmt = stmt.order_by(Quest.title.asc())
    elif sort_by == "popularity":
        stmt = stmt.order_by(func.coalesce(Quest.published_at, datetime.min).desc())
    else:
        stmt = stmt.order_by(Quest.created_at.desc())

    offset = (page - 1) * per_page
    stmt = stmt.offset(offset).limit(per_page)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{quest_id}/meta", response_model=QuestOut, summary="Get quest metadata")
async def get_quest_meta(
    quest_id: UUID,
    _: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
) -> QuestOut:
    q = await db.get(Quest, quest_id)
    if not q:
        raise HTTPException(status_code=404, detail="Quest not found")
    return q


@router.patch("/{quest_id}/meta", response_model=QuestOut, summary="Update quest metadata")
async def patch_quest_meta(
    quest_id: UUID,
    body: QuestUpdate,
    request: Request,
    current: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
) -> QuestOut:
    q = await db.get(Quest, quest_id)
    if not q:
        raise HTTPException(status_code=404, detail="Quest not found")
    before = {
        "title": q.title,
        "subtitle": q.subtitle,
        "description": q.description,
        "cover_image": q.cover_image,
        "price": q.price,
        "is_premium_only": q.is_premium_only,
        "allow_comments": q.allow_comments,
    }
    # обновляем только переданные поля
    upd = body.model_dump(exclude_unset=True)
    for k, v in upd.items():
        if hasattr(q, k):
            setattr(q, k, v)
    await audit_log(
        db,
        actor_id=str(getattr(current, "id", "")),
        action="quest_meta_update",
        resource_type="quest",
        resource_id=str(quest_id),
        before=before,
        after=upd,
        request=request,
    )
    await db.commit()
    await db.commit()
    return q
