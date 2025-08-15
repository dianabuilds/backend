import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.user import User


@pytest.mark.asyncio
async def test_publish_permissions(client: AsyncClient, db_session: AsyncSession, test_user: User, moderator_user: User):
    # Create another regular user
    other = User(
        email="other@example.com",
        username="other",
        password_hash=get_password_hash("Password123"),
        is_active=True,
    )
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)

    token_author = create_access_token(test_user.id)
    token_other = create_access_token(other.id)
    token_mod = create_access_token(moderator_user.id)

    # Author creates a quest
    resp = await client.post("/quests", json={"title": "Q1"}, headers={"Authorization": f"Bearer {token_author}"})
    assert resp.status_code == 200
    quest1 = resp.json()["id"]

    # Author can publish their quest
    resp = await client.post(f"/quests/{quest1}/publish", headers={"Authorization": f"Bearer {token_author}"})
    assert resp.status_code == 200
    assert resp.json()["is_draft"] is False

    # Create another draft quest
    resp = await client.post("/quests", json={"title": "Q2"}, headers={"Authorization": f"Bearer {token_author}"})
    assert resp.status_code == 200
    quest2 = resp.json()["id"]

    # Regular user cannot publish someone else's quest
    resp = await client.post(f"/quests/{quest2}/publish", headers={"Authorization": f"Bearer {token_other}"})
    assert resp.status_code == 403

    # Moderator can publish someone else's quest
    resp = await client.post(f"/quests/{quest2}/publish", headers={"Authorization": f"Bearer {token_mod}"})
    assert resp.status_code == 200
    assert resp.json()["is_draft"] is False
