from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.main import UPLOADS_DIR


@pytest.mark.asyncio
async def test_uploads_cache_control(client: AsyncClient) -> None:
    file_path = UPLOADS_DIR / "test.txt"
    file_path.write_text("hi")
    try:
        response = await client.get("/static/uploads/test.txt")
    finally:
        file_path.unlink()
    assert response.status_code == 200
    cache_control = response.headers.get("cache-control")
    assert cache_control is not None
    assert "max-age" in cache_control
