import pytest
from datetime import datetime, timedelta

from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_conflict_active_restriction(client, moderator_user, test_user):
    token = create_access_token(moderator_user.id)
    payload = {"user_id": str(test_user.id), "type": "post_restrict"}
    resp = await client.post(
        "/admin/restrictions",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    resp = await client.post(
        "/admin/restrictions",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_expired_restriction_allows_new(client, moderator_user, test_user):
    token = create_access_token(moderator_user.id)
    past = datetime.utcnow() - timedelta(days=1)
    payload = {
        "user_id": str(test_user.id),
        "type": "post_restrict",
        "expires_at": past.isoformat(),
    }
    resp = await client.post(
        "/admin/restrictions",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    resp = await client.post(
        "/admin/restrictions",
        json={"user_id": str(test_user.id), "type": "post_restrict"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
