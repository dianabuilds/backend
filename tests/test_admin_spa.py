import pytest


@pytest.mark.asyncio
async def test_admin_spa_placeholder(client):
    resp = await client.get("/admin")
    assert resp.status_code == 200
    assert "Admin SPA build not found" in resp.text
