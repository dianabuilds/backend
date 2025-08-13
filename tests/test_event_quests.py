import pytest
from datetime import datetime, timedelta
from sqlalchemy.future import select

from app.core.security import get_password_hash, create_access_token
from app.models.user import User
from app.models.node import Node
from app.models.event_quest import (
    EventQuest,
    EventQuestRewardType,
    EventQuestCompletion,
)
from app.models.notification import Notification
from app.services.quests import check_quest_completion


@pytest.mark.asyncio
async def test_event_quest_flow(client, db_session, test_user):
    token = create_access_token(test_user.id)
    resp = await client.post(
        "/nodes",
        json={
            "title": "Target",
            "content": "A",
            "is_public": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    slug = resp.json()["slug"]
    result = await db_session.execute(select(Node).where(Node.slug == slug))
    node = result.scalars().first()

    starts = datetime.utcnow() - timedelta(minutes=1)
    ends = datetime.utcnow() + timedelta(hours=1)

    quest = EventQuest(
        title="Event",
        target_node_id=node.id,
        hints_tags=[],
        hints_keywords=[],
        hints_trace=[],
        starts_at=starts,
        expires_at=ends,
        max_rewards=1,
        reward_type=EventQuestRewardType.premium,
        is_active=True,
    )
    db_session.add(quest)
    await db_session.commit()
    await db_session.refresh(quest)

    user1 = User(
        email="u1@example.com",
        username="u1",
        password_hash=get_password_hash("pass"),
        is_active=True,
    )
    user2 = User(
        email="u2@example.com",
        username="u2",
        password_hash=get_password_hash("pass"),
        is_active=True,
    )
    user3 = User(
        email="u3@example.com",
        username="u3",
        password_hash=get_password_hash("pass"),
        is_active=True,
    )
    db_session.add_all([user1, user2, user3])
    await db_session.commit()

    await check_quest_completion(db_session, user1, node)
    await db_session.refresh(user1)
    assert user1.is_premium
    nres = await db_session.execute(select(Notification).where(Notification.user_id == user1.id))
    note1 = nres.scalars().first()
    assert note1 and "among the first" in note1.message

    await check_quest_completion(db_session, user2, node)
    await db_session.refresh(user2)
    assert not user2.is_premium
    nres = await db_session.execute(select(Notification).where(Notification.user_id == user2.id))
    note2 = nres.scalars().first()
    assert note2 and "rewards are exhausted" in note2.message

    quest.is_active = False
    await db_session.commit()
    await db_session.refresh(quest)
    assert not quest.is_active

    await check_quest_completion(db_session, user3, node)
    await db_session.refresh(user3)
    assert not user3.is_premium
    res = await db_session.execute(
        select(EventQuestCompletion).where(EventQuestCompletion.quest_id == quest.id)
    )
    completions = res.scalars().all()
    assert len(completions) == 2
    nres = await db_session.execute(select(Notification).where(Notification.user_id == user3.id))
    assert nres.scalars().first() is None
