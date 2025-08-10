import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import create_access_token
from app.models.node import Node


async def _create_node(client: AsyncClient, token: str, title: str, tags: list[str] | None = None):
    payload = {
        "title": title,
        "content_format": "text",
        "content": title,
        "is_public": True,
        "is_recommendable": True,
        "tags": tags or [],
    }
    resp = await client.post("/nodes", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    return resp.json()["slug"]


@pytest.mark.asyncio
async def test_admin_nodes_filters(client: AsyncClient, db_session: AsyncSession, test_user, moderator_user):
    token_user = create_access_token(test_user.id)
    token_mod = create_access_token(moderator_user.id)

    slug1 = await _create_node(client, token_user, "A", ["tag1", "tag2"])
    slug2 = await _create_node(client, token_user, "B", ["tag1"])
    slug3 = await _create_node(client, token_mod, "C", ["tag2"])

    resp = await client.get(
        "/admin/nodes",
        params={"author": str(test_user.id)},
        headers={"Authorization": f"Bearer {token_mod}"},
    )
    assert resp.status_code == 200
    slugs = {n["slug"] for n in resp.json()}
    assert slugs == {slug1, slug2}

    resp = await client.get(
        "/admin/nodes",
        params={"tags": "tag1,tag2", "match": "any"},
        headers={"Authorization": f"Bearer {token_mod}"},
    )
    assert resp.status_code == 200
    slugs = {n["slug"] for n in resp.json()}
    assert slugs == {slug1, slug2, slug3}

    resp = await client.get(
        "/admin/nodes",
        params={"tags": "tag1,tag2", "match": "all"},
        headers={"Authorization": f"Bearer {token_mod}"},
    )
    assert resp.status_code == 200
    slugs = {n["slug"] for n in resp.json()}
    assert slugs == {slug1}


@pytest.mark.asyncio
async def test_admin_nodes_bulk_operations(client: AsyncClient, db_session: AsyncSession, test_user, moderator_user):
    token_user = create_access_token(test_user.id)
    token_mod = create_access_token(moderator_user.id)

    slug1 = await _create_node(client, token_user, "A")
    slug2 = await _create_node(client, token_user, "B")

    result = await db_session.execute(select(Node).where(Node.slug.in_([slug1, slug2])))
    nodes = {n.slug: n for n in result.scalars().all()}
    ids = [str(nodes[slug1].id), str(nodes[slug2].id)]

    resp = await client.post(
        "/admin/nodes/bulk",
        json={"ids": ids, "op": "hide"},
        headers={"Authorization": f"Bearer {token_mod}"},
    )
    assert resp.status_code == 200
    await db_session.refresh(nodes[slug1])
    await db_session.refresh(nodes[slug2])
    assert not nodes[slug1].is_visible and not nodes[slug2].is_visible

    resp = await client.post(
        "/admin/nodes/bulk",
        json={"ids": ids, "op": "show"},
        headers={"Authorization": f"Bearer {token_mod}"},
    )
    assert resp.status_code == 200
    await db_session.refresh(nodes[slug1])
    await db_session.refresh(nodes[slug2])
    assert nodes[slug1].is_visible and nodes[slug2].is_visible


@pytest.mark.asyncio
async def test_admin_recompute_embedding(client: AsyncClient, db_session: AsyncSession, test_user):
    token = create_access_token(test_user.id)
    slug = await _create_node(client, token, "Emb", ["x"])

    result = await db_session.execute(select(Node).where(Node.slug == slug))
    node = result.scalars().first()
    assert node is not None
    dim = len(node.embedding_vector)
    node.embedding_vector = [0.0] * dim
    await db_session.commit()

    resp = await client.post(
        f"/admin/nodes/{node.id}/embedding/recompute",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    await db_session.refresh(node)
    assert node.embedding_vector is not None
    assert any(v != 0 for v in node.embedding_vector)
