import pytest
from datetime import datetime, timedelta
from sqlalchemy.future import select

from app.core.security import get_password_hash, create_access_token
from app.domains.users.infrastructure.models.user import User
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.quests.infrastructure.models.event_quest_models import (
    EventQuest,
    EventQuestRewardType,
    EventQuestCompletion,
)
from app.domains.notifications.infrastructure.models.notification_models import (
    Notification,
)
from app.domains.quests.application.helpers import check_quest_completion
from app.domains.workspaces.infrastructure.models import Workspace


@pytest.mark.asyncio
async def test_event_quest_flow(client, db_session, test_user):
    token = create_access_token(test_user.id)
    ws = Workspace(name="ws", slug="ws", owner_user_id=test_user.id)
    db_session.add(ws)
    await db_session.commit()
    await db_session.refresh(ws)

    resp = await client.post(
        "/nodes",
        params={"workspace_id": str(ws.id)},
        json={"title": "Target", "nodes": "A", "is_public": True},
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
        workspace_id=ws.id,
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

    await check_quest_completion(db_session, user1, node, ws.id)
    await db_session.refresh(user1)
    assert user1.is_premium
    nres = await db_session.execute(select(Notification).where(Notification.user_id == user1.id))
    note1 = nres.scalars().first()
    assert note1 and "among the first" in note1.message

    await check_quest_completion(db_session, user2, node, ws.id)
    await db_session.refresh(user2)
    assert not user2.is_premium
    nres = await db_session.execute(select(Notification).where(Notification.user_id == user2.id))
    note2 = nres.scalars().first()
    assert note2 and "rewards are exhausted" in note2.message

    quest.is_active = False
    await db_session.commit()
    await db_session.refresh(quest)
    assert not quest.is_active

    await check_quest_completion(db_session, user3, node, ws.id)
    await db_session.refresh(user3)
    assert not user3.is_premium
    res = await db_session.execute(
        select(EventQuestCompletion).where(
            EventQuestCompletion.quest_id == quest.id,
            EventQuestCompletion.workspace_id == ws.id,
        )
    )
    completions = res.scalars().all()
    assert len(completions) == 2
    nres = await db_session.execute(select(Notification).where(Notification.user_id == user3.id))
    assert nres.scalars().first() is None
