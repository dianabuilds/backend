import pytest
from datetime import datetime, timedelta
from sqlalchemy.future import select

from app.core.security import get_password_hash
from app.models.user import User
from app.models.node import Node
from app.models.event_quest import EventQuest
from app.models.notification import Notification
from app.models.event_quest import EventQuestCompletion
from app.services.quests import check_quest_completion


@pytest.mark.asyncio
async def test_event_quest_flow(client, db_session):
    admin = User(
        email="admin@example.com",
        username="admin",
        password_hash=get_password_hash("AdminPass123"),
        role="admin",
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()

    resp = await client.post(
        "/auth/login",
        json={"username": "admin", "password": "AdminPass123"},
    )
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        "/nodes",
        json={"title": "Target", "content_format": "text", "content": "A", "is_public": True},
        headers=headers,
    )
    slug = resp.json()["slug"]
    result = await db_session.execute(select(Node).where(Node.slug == slug))
    node = result.scalars().first()

    starts = datetime.utcnow() - timedelta(minutes=1)
    ends = datetime.utcnow() + timedelta(hours=1)

    resp = await client.post(
        "/admin/event-quests/new",
        data={
            "title": "Event",
            "target_node": str(node.id),
            "hints_tags": "",
            "hints_keywords": "",
            "hints_trace": "",
            "starts_at": starts.isoformat(timespec="minutes"),
            "expires_at": ends.isoformat(timespec="minutes"),
            "max_rewards": "1",
            "reward_type": "premium",
            "is_active": "on",
        },
        cookies={"token": token},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    res = await db_session.execute(select(EventQuest).where(EventQuest.title == "Event"))
    quest = res.scalars().first()
    assert quest is not None and quest.is_active

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

    resp = await client.post(
        f"/admin/event-quests/{quest.id}/edit",
        data={
            "title": "Event",
            "target_node": str(node.id),
            "hints_tags": "",
            "hints_keywords": "",
            "hints_trace": "",
            "starts_at": starts.isoformat(timespec="minutes"),
            "expires_at": ends.isoformat(timespec="minutes"),
            "max_rewards": "1",
            "reward_type": "premium",
        },
        cookies={"token": token},
        follow_redirects=False,
    )
    assert resp.status_code == 303
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
