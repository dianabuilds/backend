import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.achievement import Achievement, UserAchievement
from app.models.node import Node
from app.models.notification import Notification
from app.services.achievements import AchievementsService


@pytest.mark.asyncio
async def test_achievements_flow(client: AsyncClient, db_session: AsyncSession, auth_headers, test_user):
    a1 = Achievement(
        code="first_dive",
        title="First cave",
        description="start",
        icon="🌌",
        condition={"type": "event_count", "event": "visit_node", "count": 1},
        visible=True,
    )
    a2 = Achievement(
        code="hundred_nodes",
        title="Explorer",
        description="100 nodes",
        icon="🧭",
        condition={"type": "event_count", "event": "visit_node", "count": 100},
        visible=True,
    )
    db_session.add_all([a1, a2])
    await db_session.commit()

    resp = await client.get("/achievements", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all(not item["unlocked"] for item in data)

    unlocked = await AchievementsService.process_event(
        db_session, test_user.id, "visit_node", {}
    )
    assert len(unlocked) == 1 and unlocked[0].code == "first_dive"

    resp = await client.get("/achievements", headers=auth_headers)
    data = resp.json()
    first = next(a for a in data if a["code"] == "first_dive")
    assert first["unlocked"] and first["unlocked_at"] is not None
    second = next(a for a in data if a["code"] == "hundred_nodes")
    assert not second["unlocked"]

    result = await db_session.execute(select(Notification).where(Notification.user_id == test_user.id))
    notifs = result.scalars().all()
    assert any(n.message == "First cave" for n in notifs)


@pytest.mark.asyncio
async def test_nodes_created_achievement(client: AsyncClient, db_session: AsyncSession, auth_headers, test_user):
    ach = Achievement(
        code="five_nodes",
        title="Contributor",
        description="Create 5 nodes",
        icon="📝",
        condition={"type": "nodes_created", "count": 5},
        visible=True,
    )
    db_session.add(ach)
    await db_session.commit()

    for i in range(5):
        node = Node(
            title=f"Node {i}",
            content={},
            author_id=test_user.id,
        )
        db_session.add(node)
        await db_session.commit()
        await AchievementsService.process_event(db_session, test_user.id, "node_created")

    resp = await client.get("/achievements", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    created = next(a for a in data if a["code"] == "five_nodes")
    assert created["unlocked"]
