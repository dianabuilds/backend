import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cors_preflight_login(client: AsyncClient) -> None:
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    }
    response = await client.options("/auth/login", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

