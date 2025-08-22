import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.domains.users.infrastructure.models.user import User


@pytest.mark.asyncio
async def test_default_flags_present(client: AsyncClient, admin_user: User) -> None:
    token = create_access_token(admin_user.id)
    resp = await client.get(
        "/admin/flags", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    keys = {f["key"] for f in data}
    assert "payments" in keys
    assert "moderation.enabled" in keys
