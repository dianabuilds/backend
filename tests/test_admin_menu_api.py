import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.models.user import User


@pytest.mark.asyncio
async def test_menu_requires_auth(client: AsyncClient):
    resp = await client.get("/admin/menu")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_menu_forbidden(client: AsyncClient, test_user: User):
    token = create_access_token(test_user.id)
    resp = await client.get("/admin/menu", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_menu_success_and_etag(client: AsyncClient, admin_user: User):
    token = create_access_token(admin_user.id)
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.get("/admin/menu", headers=headers)
    assert resp.status_code == 200
    etag = resp.headers.get("ETag")
    assert etag
    data = resp.json()
    assert "items" in data and isinstance(data["items"], list)
    headers["If-None-Match"] = etag
    resp2 = await client.get("/admin/menu", headers=headers)
    assert resp2.status_code == 304


@pytest.mark.asyncio
async def test_menu_roles_and_flags(client: AsyncClient, admin_user: User, moderator_user: User):
    token_admin = create_access_token(admin_user.id)
    token_mod = create_access_token(moderator_user.id)
    resp_admin = await client.get(
        "/admin/menu",
        headers={"Authorization": f"Bearer {token_admin}", "X-Feature-Flags": "extra"},
    )
    resp_mod = await client.get(
        "/admin/menu", headers={"Authorization": f"Bearer {token_mod}"}
    )
    assert resp_admin.status_code == 200
    assert resp_mod.status_code == 200
    ids_admin = [i["id"] for i in resp_admin.json()["items"]]
    ids_mod = [i["id"] for i in resp_mod.json()["items"]]
    assert "admin-only" in ids_admin
    assert "admin-only" not in ids_mod
    group_admin = next(i for i in resp_admin.json()["items"] if i["id"] == "group")
    group_mod = next(i for i in resp_mod.json()["items"] if i["id"] == "group")
    child_admin = [c["id"] for c in group_admin["children"]]
    child_mod = [c["id"] for c in group_mod["children"]]
    assert "flagged" in child_admin
    assert "flagged" not in child_mod
