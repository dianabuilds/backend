from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.quest import Quest, QuestPurchase, QuestProgress
from app.models.node import Node
from app.models.user import User
from app.schemas.quest import (
    QuestCreate,
    QuestUpdate,
    QuestOut,
    QuestProgressOut,
)
from app.schemas.node import NodeOut
from app.services.quests import has_access

router = APIRouter(prefix="/quests", tags=["quests"])


@router.get("", response_model=list[QuestOut])
async def list_quests(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Quest).where(Quest.is_draft == False, Quest.is_deleted == False)
    )
    return result.scalars().all()


@router.get("/{slug}", response_model=QuestOut)
async def get_quest(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Quest).where(Quest.slug == slug, Quest.is_deleted == False))
    quest = result.scalars().first()
    if not quest or (quest.is_draft and quest.author_id != current_user.id):
        raise HTTPException(status_code=404, detail="Quest not found")
    return quest


@router.post("", response_model=QuestOut)
async def create_quest(
    payload: QuestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    quest = Quest(
        title=payload.title,
        subtitle=payload.subtitle,
        description=payload.description,
        cover_image=payload.cover_image,
        tags=payload.tags,
        price=payload.price,
        is_premium_only=payload.is_premium_only,
        entry_node_id=payload.entry_node_id,
        nodes=payload.nodes,
        custom_transitions=payload.custom_transitions,
        allow_comments=payload.allow_comments,
        author_id=current_user.id,
    )
    db.add(quest)
    await db.commit()
    await db.refresh(quest)
    return quest


@router.put("/{quest_id}", response_model=QuestOut)
async def update_quest(
    quest_id: UUID,
    payload: QuestUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Quest).where(Quest.id == quest_id, Quest.is_deleted == False))
    quest = result.scalars().first()
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    if quest.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    data = payload.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(quest, field, value)
    await db.commit()
    await db.refresh(quest)
    return quest


@router.post("/{quest_id}/publish", response_model=QuestOut)
async def publish_quest(
    quest_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Quest).where(Quest.id == quest_id, Quest.is_deleted == False))
    quest = result.scalars().first()
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    if quest.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    quest.is_draft = False
    quest.published_at = datetime.utcnow()
    await db.commit()
    await db.refresh(quest)
    return quest


@router.delete("/{quest_id}", response_model=dict)
async def delete_quest(
    quest_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Quest).where(Quest.id == quest_id, Quest.is_deleted == False))
    quest = result.scalars().first()
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    if quest.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    quest.is_deleted = True
    await db.commit()
    return {"status": "ok"}


@router.post("/{quest_id}/start", response_model=QuestProgressOut)
async def start_quest(
    quest_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Quest).where(Quest.id == quest_id, Quest.is_deleted == False))
    quest = result.scalars().first()
    if not quest or quest.is_draft:
        raise HTTPException(status_code=404, detail="Quest not found")
    if not await has_access(db, current_user, quest):
        raise HTTPException(status_code=403, detail="No access")
    res = await db.execute(
        select(QuestProgress).where(
            QuestProgress.quest_id == quest.id,
            QuestProgress.user_id == current_user.id,
        )
    )
    progress = res.scalars().first()
    if progress:
        progress.current_node_id = quest.entry_node_id
        progress.started_at = datetime.utcnow()
    else:
        progress = QuestProgress(
            quest_id=quest.id,
            user_id=current_user.id,
            current_node_id=quest.entry_node_id,
        )
        db.add(progress)
    await db.commit()
    await db.refresh(progress)
    return progress


@router.get("/{quest_id}/progress", response_model=QuestProgressOut)
async def get_progress(
    quest_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(QuestProgress).where(
            QuestProgress.quest_id == quest_id,
            QuestProgress.user_id == current_user.id,
        )
    )
    progress = res.scalars().first()
    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found")
    return progress


@router.get("/{quest_id}/nodes/{node_id}", response_model=NodeOut)
async def get_quest_node(
    quest_id: UUID,
    node_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Quest).where(Quest.id == quest_id, Quest.is_deleted == False))
    quest = result.scalars().first()
    if not quest or quest.is_draft:
        raise HTTPException(status_code=404, detail="Quest not found")
    if node_id not in quest.nodes:
        raise HTTPException(status_code=404, detail="Node not part of quest")
    if not await has_access(db, current_user, quest):
        raise HTTPException(status_code=403, detail="No access")
    result = await db.execute(select(Node).where(Node.id == node_id))
    node = result.scalars().first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    res = await db.execute(
        select(QuestProgress).where(
            QuestProgress.quest_id == quest.id,
            QuestProgress.user_id == current_user.id,
        )
    )
    progress = res.scalars().first()
    if progress:
        progress.current_node_id = node.id
        progress.updated_at = datetime.utcnow()
        await db.commit()
    return node


@router.post("/{quest_id}/buy", response_model=dict)
async def buy_quest(
    quest_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Quest).where(Quest.id == quest_id, Quest.is_deleted == False))
    quest = result.scalars().first()
    if not quest or quest.is_draft:
        raise HTTPException(status_code=404, detail="Quest not found")
    if quest.price in (None, 0):
        return {"status": "free"}
    res = await db.execute(
        select(QuestPurchase).where(
            QuestPurchase.quest_id == quest.id,
            QuestPurchase.user_id == current_user.id,
        )
    )
    purchase = res.scalars().first()
    if purchase:
        return {"status": "already"}
    purchase = QuestPurchase(quest_id=quest.id, user_id=current_user.id)
    db.add(purchase)
    await db.commit()
    return {"status": "ok"}
