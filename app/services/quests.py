from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quest import Quest, QuestCompletion, QuestRewardType
from app.models.node import Node
from app.models.user import User
from app.services.notifications import create_notification
from app.models.notification import NotificationType


async def check_quest_completion(db: AsyncSession, user: User, node: Node) -> None:
    now = datetime.utcnow()
    result = await db.execute(
        select(Quest).where(
            Quest.is_active == True,  # noqa: E712
            Quest.target_node_id == node.id,
            Quest.starts_at <= now,
            Quest.expires_at >= now,
        )
    )
    quests = result.scalars().all()
    if not quests:
        return
    for quest in quests:
        res = await db.execute(
            select(QuestCompletion).where(
                QuestCompletion.quest_id == quest.id,
                QuestCompletion.user_id == user.id,
            )
        )
        if res.scalars().first():
            continue
        completion = QuestCompletion(
            quest_id=quest.id,
            user_id=user.id,
            node_id=node.id,
        )
        db.add(completion)
        await db.commit()
        await db.refresh(completion)
        count_res = await db.execute(
            select(func.count(QuestCompletion.id)).where(QuestCompletion.quest_id == quest.id)
        )
        count = count_res.scalar_one()
        if count <= quest.max_rewards:
            if quest.reward_type == QuestRewardType.premium:
                user.is_premium = True
                user.premium_until = (user.premium_until or now) + timedelta(days=7)
                await db.commit()
            # Send reward notification
            await create_notification(
                db,
                user.id,
                title=f"Quest completed: {quest.title}",
                message="You were among the first to finish the quest!",
                type=NotificationType.quest,
            )
        else:
            await create_notification(
                db,
                user.id,
                title=f"Quest completed: {quest.title}",
                message="Quest completed, but rewards are exhausted.",
                type=NotificationType.quest,
            )

