import pytest
from httpx import AsyncClient

from app.core.metrics import metrics_storage
from app.models.user import User


async def login(client: AsyncClient, username: str, password: str = "Password123") -> dict:
    resp = await client.post("/auth/login", json={"username": username, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_metrics_summary(client: AsyncClient, admin_user: User):
    headers = await login(client, "admin")
    metrics_storage.reset()
    await client.get("/health")
    await client.get("/not-found")
    resp = await client.get("/admin/metrics/summary", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["count_429"] == 0
    assert 0.4 < data["error_rate"] < 0.6
