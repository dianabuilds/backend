import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4

from app.domains.achievements.infrastructure.models.achievement_models import Achievement, UserAchievement
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.notifications.infrastructure.models.notification_models import Notification
from app.domains.achievements.application.achievements_service import AchievementsService
from app.domains.workspaces.infrastructure.models import Workspace


@pytest.mark.asyncio
async def test_achievements_flow(client: AsyncClient, db_session: AsyncSession, auth_headers, test_user):
    ws = Workspace(name="ws", slug="ws", owner_user_id=test_user.id)
    db_session.add(ws)
    await db_session.commit()
    await db_session.refresh(ws)

    a1 = Achievement(
        code="first_dive",
        title="First cave",
        description="start",
        icon="🌌",
        condition={"type": "event_count", "event": "visit_node", "count": 1},
        visible=True,
        workspace_id=ws.id,
    )
    a2 = Achievement(
        code="hundred_nodes",
        title="Explorer",
        description="100 nodes",
        icon="🧭",
        condition={"type": "event_count", "event": "visit_node", "count": 100},
        visible=True,
        workspace_id=ws.id,
    )
    db_session.add_all([a1, a2])
    await db_session.commit()

    resp = await client.get(
        "/achievements",
        headers=auth_headers,
        params={"workspace_id": str(ws.id)},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all(not item["unlocked"] for item in data)

    unlocked = await AchievementsService.process_event(
        db_session, test_user.id, "visit_node", {}
    )
    assert len(unlocked) == 1 and unlocked[0].code == "first_dive"

    resp = await client.get(
        "/achievements",
        headers=auth_headers,
        params={"workspace_id": str(ws.id)},
    )
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
    ws = Workspace(name="ws", slug="ws2", owner_user_id=test_user.id)
    db_session.add(ws)
    await db_session.commit()
    await db_session.refresh(ws)

    ach = Achievement(
        code="five_nodes",
        title="Contributor",
        description="Create 5 nodes",
        icon="📝",
        condition={"type": "nodes_created", "count": 5},
        visible=True,
        workspace_id=ws.id,
    )
    db_session.add(ach)
    await db_session.commit()

    for i in range(5):
        node = Node(
            title=f"Node {i}",
            content={},
            author_id=test_user.id,
            workspace_id=ws.id,
        )
        db_session.add(node)
        await db_session.commit()
        await AchievementsService.process_event(db_session, test_user.id, "node_created")

    resp = await client.get(
        "/achievements",
        headers=auth_headers,
        params={"workspace_id": str(ws.id)},
    )
    assert resp.status_code == 200
    data = resp.json()
    created = next(a for a in data if a["code"] == "five_nodes")
    assert created["unlocked"]


@pytest.mark.asyncio
async def test_achievements_foreign_workspace_forbidden(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_headers,
    test_user,
):
    """User cannot access achievements of a workspace they don't belong to."""
    ws1 = Workspace(name="ws1", slug="ws1", owner_user_id=test_user.id)
    ws2 = Workspace(name="ws2", slug="ws2", owner_user_id=uuid4())
    db_session.add_all([ws1, ws2])
    await db_session.commit()

    resp = await client.get(
        "/achievements",
        headers=auth_headers,
        params={"workspace_id": str(ws2.id)},
    )
    assert resp.status_code == 404
