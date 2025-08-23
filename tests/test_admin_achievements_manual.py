import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.achievements.infrastructure.models.achievement_models import Achievement, UserAchievement
from app.domains.users.infrastructure.models.user import User
from app.domains.workspaces.infrastructure.models import Workspace


@pytest.mark.asyncio
async def test_admin_grant_and_revoke(
    client: AsyncClient, db_session: AsyncSession, admin_user: User, test_user: User
):
    ws = Workspace(name="ws", slug="ws_admin", owner_user_id=admin_user.id)
    db_session.add(ws)
    await db_session.commit()
    await db_session.refresh(ws)

    ach = Achievement(
        code="manual_test",
        title="Manual",
        description="manual",
        icon="",
        condition={"type": "event_count", "event": "x", "count": 1},
        visible=True,
        workspace_id=ws.id,
    )
    db_session.add(ach)
    await db_session.commit()
    await db_session.refresh(ach)

    # authenticate to obtain CSRF token and cookies
    login_resp = await client.post(
        "/auth/login",
        json={"username": "admin", "password": "Password123"},
    )
    csrf = login_resp.json()["csrf_token"]
    token = client.cookies.get("access_token")
    headers = {
        "Authorization": f"Bearer {token}",
        "X-CSRF-Token": csrf,
    }

    resp = await client.post(
        f"/admin/achievements/{ach.id}/grant",
        headers=headers,
        json={"user_id": str(test_user.id)},
        params={"workspace_id": str(ws.id)},
    )
    assert resp.status_code == 200
    assert resp.json()["granted"] is True

    result = await db_session.execute(
        select(UserAchievement).where(
            UserAchievement.user_id == test_user.id,
            UserAchievement.achievement_id == ach.id,
        )
    )
    assert result.scalars().first() is not None

    resp = await client.post(
        f"/admin/achievements/{ach.id}/revoke",
        headers=headers,
        json={"user_id": str(test_user.id)},
        params={"workspace_id": str(ws.id)},
    )
    assert resp.status_code == 200
    assert resp.json()["revoked"] is True

    result = await db_session.execute(
        select(UserAchievement).where(
            UserAchievement.user_id == test_user.id,
            UserAchievement.achievement_id == ach.id,
        )
    )
    assert result.scalars().first() is None
