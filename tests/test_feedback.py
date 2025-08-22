import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_feedback_flow(client: AsyncClient, auth_headers):
    # Create a public node
    resp = await client.post(
        "/nodes",
        json={
            "title": "test",
            "nodes": "test",
            "is_public": True,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    slug = resp.json()["slug"]

    # Post feedback
    resp = await client.post(
        f"/nodes/{slug}/feedback",
        json={"nodes": "hi"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    fb_id = resp.json()["id"]

    # List feedback
    resp = await client.get(f"/nodes/{slug}/feedback", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["nodes"] == "hi"

    # Delete feedback
    resp = await client.delete(
        f"/nodes/{slug}/feedback/{fb_id}", headers=auth_headers
    )
    assert resp.status_code == 200

    # Ensure hidden
    resp = await client.get(f"/nodes/{slug}/feedback", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_feedback_disabled(client: AsyncClient, auth_headers):
    # Create node with feedback disabled
    resp = await client.post(
        "/nodes",
        json={
            "title": "nfb",
            "nodes": "nfb",
            "is_public": True,
            "allow_feedback": False,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    slug = resp.json()["slug"]

    # Attempt to post feedback
    resp = await client.post(
        f"/nodes/{slug}/feedback",
        json={"nodes": "hi"},
        headers=auth_headers,
    )
    assert resp.status_code == 403
