import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User
from app.services import nft as nft_service


@pytest.fixture(autouse=True)
def patch_nft_verifier(monkeypatch):
    async def yes(user, req):
        return True

    async def no(user, req):
        return False

    monkeypatch.setattr(nft_service, "user_has_nft", no)
    monkeypatch.setattr("app.api.nodes.user_has_nft", no)
    monkeypatch.setattr("app.engine.filters.user_has_nft", no)

    def setter(allow: bool):
        func = yes if allow else no
        monkeypatch.setattr(nft_service, "user_has_nft", func)
        monkeypatch.setattr("app.api.nodes.user_has_nft", func)
        monkeypatch.setattr("app.engine.filters.user_has_nft", func)

    return setter


async def _create_user(db: AsyncSession, client: AsyncClient, username: str, wallet: str | None = None):
    user = User(
        email=f"{username}@example.com",
        username=username,
        password_hash=get_password_hash("pass"),
        is_active=True,
        wallet_address=wallet,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    resp = await client.post(
        "/auth/login", json={"username": username, "password": "pass"}
    )
    token = resp.json()["access_token"]
    return user, {"Authorization": f"Bearer {token}"}


async def _create_node(client: AsyncClient, headers: dict) -> str:
    resp = await client.post(
        "/nodes",
        json={
            "title": "NFT gated",
            "content": "nft",
            "is_public": True,
            "nft_required": "TEST",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    return resp.json()["slug"]


@pytest.mark.asyncio
async def test_node_denied_without_nft(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict,
    patch_nft_verifier,
):
    slug = await _create_node(client, auth_headers)
    _, headers = await _create_user(db_session, client, "nftless", wallet="0xabc")
    patch_nft_verifier(False)
    r = await client.get(f"/nodes/{slug}", headers=headers)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_node_allowed_with_nft(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict,
    patch_nft_verifier,
):
    slug = await _create_node(client, auth_headers)
    _, headers = await _create_user(db_session, client, "holder", wallet="0xabc")
    patch_nft_verifier(True)
    r = await client.get(f"/nodes/{slug}", headers=headers)
    assert r.status_code == 200
    assert r.json()["slug"] == slug
