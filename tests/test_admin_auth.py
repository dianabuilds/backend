from datetime import datetime, timedelta

import jwt
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token
from app.models.moderation import UserRestriction


@pytest.mark.asyncio
async def test_admin_auth_flow(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user,
    moderator_user,
    admin_user,
):
    url = "/admin/cache/stats"

    # missing token
    resp = await client.get(url)
    assert resp.status_code == 401
    assert resp.headers["WWW-Authenticate"] == "Bearer"
    assert resp.json()["error"]["code"] == "AUTH_REQUIRED"

    # invalid token
    resp = await client.get(url, headers={"Authorization": "Bearer bad"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_TOKEN"

    # expired token
    past = datetime.utcnow() - timedelta(hours=1)
    expired = jwt.encode(
        {"sub": str(moderator_user.id), "iat": past, "nbf": past, "exp": past},
        settings.jwt.secret,
        algorithm=settings.jwt.algorithm,
    )
    resp = await client.get(url, headers={"Authorization": f"Bearer {expired}"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "TOKEN_EXPIRED"

    # user role forbidden
    token_user = create_access_token(test_user.id)
    resp = await client.get(url, headers={"Authorization": f"Bearer {token_user}"})
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"

    # moderator allowed
    token_mod = create_access_token(moderator_user.id)
    resp = await client.get(url, headers={"Authorization": f"Bearer {token_mod}"})
    assert resp.status_code == 200

    # admin allowed
    token_admin = create_access_token(admin_user.id)
    resp = await client.get(url, headers={"Authorization": f"Bearer {token_admin}"})
    assert resp.status_code == 200

    # banned moderator
    db_session.add(UserRestriction(user_id=moderator_user.id, type="ban"))
    await db_session.commit()
    banned_token = create_access_token(moderator_user.id)
    resp = await client.get(url, headers={"Authorization": f"Bearer {banned_token}"})
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"
