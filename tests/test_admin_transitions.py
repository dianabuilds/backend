import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.navigation.infrastructure.models.transition_models import NodeTransition, NodeTransitionType
from app.domains.navigation.application.cache_singleton import navcache


async def _create_node(db: AsyncSession, author, title: str) -> Node:
    node = Node(
        title=title,
        content={},
        is_public=True,
        author_id=author.id,
    )
    db.add(node)
    await db.commit()
    await db.refresh(node)
    return node


async def _create_transition(
    db: AsyncSession, from_node: Node, to_node: Node, creator
) -> NodeTransition:
    tr = NodeTransition(
        from_node_id=from_node.id,
        to_node_id=to_node.id,
        type=NodeTransitionType.manual,
        condition={},
        weight=1,
        label="t",
        created_by=creator.id,
    )
    db.add(tr)
    await db.commit()
    await db.refresh(tr)
    return tr


@pytest.mark.asyncio
async def test_list_transitions_pagination(
    client: AsyncClient, db_session: AsyncSession, moderator_user
):
    n1 = await _create_node(db_session, moderator_user, "n1")
    n2 = await _create_node(db_session, moderator_user, "n2")
    n3 = await _create_node(db_session, moderator_user, "n3")
    await _create_transition(db_session, n1, n2, moderator_user)
    await _create_transition(db_session, n1, n3, moderator_user)
    await _create_transition(db_session, n2, n3, moderator_user)
    token = create_access_token(moderator_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/admin/transitions?page=1&page_size=2", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp = await client.get("/admin/transitions?page=2&page_size=2", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = await client.get(f"/admin/transitions?from={n1.slug}", headers=headers)
    assert resp.status_code == 200
    assert all(item["from_slug"] == n1.slug for item in resp.json())


@pytest.mark.asyncio
async def test_patch_transition_rbac_and_validation(
    client: AsyncClient,
    db_session: AsyncSession,
    moderator_user,
    test_user,
):
    n1 = await _create_node(db_session, moderator_user, "n1")
    n2 = await _create_node(db_session, moderator_user, "n2")
    tr = await _create_transition(db_session, n1, n2, moderator_user)

    token_user = create_access_token(test_user.id)
    resp = await client.patch(
        f"/admin/transitions/{tr.id}",
        json={"label": "new"},
        headers={"Authorization": f"Bearer {token_user}"},
    )
    assert resp.status_code == 403

    token_mod = create_access_token(moderator_user.id)
    resp = await client.patch(
        f"/admin/transitions/{tr.id}",
        json={"condition": {"cooldown": -1}},
        headers={"Authorization": f"Bearer {token_mod}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_disable_by_node_invalidation(
    client: AsyncClient, db_session: AsyncSession, moderator_user
):
    n1 = await _create_node(db_session, moderator_user, "n1")
    n2 = await _create_node(db_session, moderator_user, "n2")
    tr = await _create_transition(db_session, n1, n2, moderator_user)

    called = {"nav": None, "comp": None}

    async def fake_nav(slug):
        called["nav"] = slug

    async def fake_comp(slug):
        called["comp"] = slug

    mp = pytest.MonkeyPatch()
    mp.setattr(navcache, "invalidate_navigation_by_node", fake_nav)
    mp.setattr(navcache, "invalidate_compass_by_node", fake_comp)

    token = create_access_token(moderator_user.id)
    resp = await client.post(
        "/admin/transitions/disable_by_node",
        json={"slug": n1.slug},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    await db_session.refresh(tr)
    assert tr.type == NodeTransitionType.locked
    assert called["nav"] == n1.slug
    assert called["comp"] == n1.slug
    mp.undo()
