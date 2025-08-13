import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import create_access_token
from app.models.tag import Tag
from app.models.node import Node
from app.services.tags import get_or_create_tags
from app.services.navcache import navcache


async def _create_node(db: AsyncSession, author, title: str, tags: list[str] | None = None) -> Node:
    node = Node(
        title=title,
        content={},
        is_public=True,
        author_id=author.id,
    )
    if tags:
        node.tags = await get_or_create_tags(db, tags)
    db.add(node)
    await db.commit()
    await db.refresh(node)
    return node


@pytest.mark.asyncio
async def test_list_tags_pagination(client: AsyncClient, db_session: AsyncSession, moderator_user):
    db_session.add_all([
        Tag(slug="t1", name="T1"),
        Tag(slug="t2", name="T2"),
        Tag(slug="t3", name="T3", is_hidden=True),
    ])
    await db_session.commit()
    token = create_access_token(moderator_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/admin/tags?page=1&page_size=2", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp = await client.get("/admin/tags?page=2&page_size=2", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = await client.get("/admin/tags?hidden=true", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["slug"] == "t3"


@pytest.mark.asyncio
async def test_create_tag_unique_and_rbac(client: AsyncClient, db_session: AsyncSession, moderator_user, test_user):
    db_session.add(Tag(slug="exist", name="Exist"))
    await db_session.commit()
    token_mod = create_access_token(moderator_user.id)
    token_user = create_access_token(test_user.id)

    resp = await client.post(
        "/admin/tags",
        json={"slug": "new", "name": "New"},
        headers={"Authorization": f"Bearer {token_user}"},
    )
    assert resp.status_code == 403

    resp = await client.post(
        "/admin/tags",
        json={"slug": "new", "name": "New"},
        headers={"Authorization": f"Bearer {token_mod}"},
    )
    assert resp.status_code == 200
    assert resp.json()["slug"] == "new"

    resp = await client.post(
        "/admin/tags",
        json={"slug": "new", "name": "New2"},
        headers={"Authorization": f"Bearer {token_mod}"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_merge_tags_reassign(client: AsyncClient, db_session: AsyncSession, moderator_user):
    n1 = await _create_node(db_session, moderator_user, "n1", ["a"])
    n2 = await _create_node(db_session, moderator_user, "n2", ["a", "b"])
    token = create_access_token(moderator_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    called = {"nav": [], "comp": []}

    async def fake_nav(slug):
        called["nav"].append(slug)

    async def fake_comp(slug):
        called["comp"].append(slug)

    mp = pytest.MonkeyPatch()
    mp.setattr(navcache, "invalidate_navigation_by_node", fake_nav)
    mp.setattr(navcache, "invalidate_compass_by_node", fake_comp)

    resp = await client.post(
        "/admin/tags/merge",
        json={"from_slug": "a", "to_slug": "b"},
        headers=headers,
    )
    assert resp.status_code == 200
    await db_session.refresh(n1)
    await db_session.refresh(n2)
    assert {t.slug for t in n1.tags} == {"b"}
    assert {t.slug for t in n2.tags} == {"b"}
    res = await db_session.execute(select(Tag).where(Tag.slug == "a"))
    assert res.scalars().first() is None
    assert set(called["nav"]) == {n1.slug, n2.slug}
    assert set(called["comp"]) == {n1.slug, n2.slug}
    mp.undo()


@pytest.mark.asyncio
async def test_detach_tag(client: AsyncClient, db_session: AsyncSession, moderator_user):
    n1 = await _create_node(db_session, moderator_user, "n1", ["a"])
    n2 = await _create_node(db_session, moderator_user, "n2", ["a"])
    token = create_access_token(moderator_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    called = {"nav": None, "comp": None}

    async def fake_nav(slug):
        called["nav"] = slug

    async def fake_comp(slug):
        called["comp"] = slug

    mp = pytest.MonkeyPatch()
    mp.setattr(navcache, "invalidate_navigation_by_node", fake_nav)
    mp.setattr(navcache, "invalidate_compass_by_node", fake_comp)

    resp = await client.post(
        f"/admin/tags/a/detach",
        json={"node_ids": [str(n1.id)]},
        headers=headers,
    )
    assert resp.status_code == 200
    await db_session.refresh(n1)
    await db_session.refresh(n2)
    assert n1.tags == []
    assert {t.slug for t in n2.tags} == {"a"}
    assert called["nav"] == n1.slug
    assert called["comp"] == n1.slug
    mp.undo()
