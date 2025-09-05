from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.domains.accounts.application.shared_objects_service import has_access
from app.domains.nodes.models import NodeItem
from app.domains.quests.access import can_view
from app.domains.quests.infrastructure.models.quest_models import Quest
from app.domains.users.infrastructure.models.user import User
from app.schemas.nodes_common import Status


async def list_public(db: AsyncSession, *, workspace_id: UUID) -> list[Quest]:
    res = await db.execute(
        select(Quest)
        .join(NodeItem, NodeItem.id == Quest.id)
        .where(
            NodeItem.type == "quest",
            NodeItem.status == Status.published,
            Quest.is_deleted.is_(False),
            Quest.workspace_id == workspace_id,
        )
        .order_by(NodeItem.published_at.desc())
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
    workspace_id: UUID,
) -> list[Quest]:
    stmt = (
        select(Quest)
        .join(NodeItem, NodeItem.id == Quest.id)
        .where(
            NodeItem.type == "quest",
            NodeItem.status == Status.published,
            Quest.is_deleted.is_(False),
            Quest.workspace_id == workspace_id,
        )
    )

    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                NodeItem.title.ilike(pattern),
                NodeItem.summary.ilike(pattern),
            )
        )

    if tags:
        for tag in tags:
            stmt = stmt.where(Quest.tags.like(f'%"{tag}"%'))

    if author_id:
        stmt = stmt.where(Quest.author_id == author_id)

    if free_only:
        stmt = stmt.where(or_(Quest.price.is_(None), Quest.price == 0))

    if premium_only:
        stmt = stmt.where(Quest.is_premium_only.is_(True))

    if sort_by == "price":
        stmt = stmt.order_by(Quest.price.asc())
    elif sort_by == "title":
        stmt = stmt.order_by(NodeItem.title.asc())
    elif sort_by == "popularity":
        stmt = stmt.order_by(func.coalesce(NodeItem.published_at, datetime.min).desc())
    else:
        stmt = stmt.order_by(NodeItem.published_at.desc())

    offset = (page - 1) * per_page
    stmt = stmt.offset(offset).limit(per_page)

    res = await db.execute(stmt)
    return list(res.scalars().all())


async def get_for_view(db: AsyncSession, *, slug: str, user: User, workspace_id: UUID) -> Quest:
    res = await db.execute(
        select(Quest).where(
            Quest.slug == slug,
            Quest.is_deleted.is_(False),
        )
    )
    quest = res.scalars().first()
    if not quest or (quest.is_draft and quest.author_id != user.id):
        raise ValueError("Quest not found")
    if quest.workspace_id != workspace_id:
        allowed = await has_access(
            db,
            object_type="quest",
            object_id=quest.id,
            account_id=workspace_id,
            permission="view",
        )
        if not allowed:
            raise PermissionError("No access")
    if not await can_view(db, quest=quest, user=user):
        raise PermissionError("No access")
    return quest
