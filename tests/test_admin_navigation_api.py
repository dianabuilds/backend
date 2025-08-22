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
async def test_run_deterministic_order(client: AsyncClient, db_session: AsyncSession, moderator_user):
    base = await _create_node(db_session, moderator_user, "base")
    n1 = await _create_node(db_session, moderator_user, "a1")
    n2 = await _create_node(db_session, moderator_user, "b2")
    await _create_transition(db_session, base, n1, moderator_user)
    await _create_transition(db_session, base, n2, moderator_user)

    token = create_access_token(moderator_user.id)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"node_slug": base.slug}

    resp1 = await client.post("/admin/navigation/run", json=payload, headers=headers)
    resp2 = await client.post("/admin/navigation/run", json=payload, headers=headers)
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    slugs1 = [t["slug"] for t in resp1.json()["transitions"]]
    slugs2 = [t["slug"] for t in resp2.json()["transitions"]]
    assert slugs1 == slugs2
    assert slugs1 == sorted(slugs1)


@pytest.mark.asyncio
async def test_invalidate_clears_cache(client: AsyncClient, db_session: AsyncSession, moderator_user):
    node = await _create_node(db_session, moderator_user, "node")
    await navcache.set_navigation("anon", node.slug, "auto", {"dummy": 1})
    assert await navcache.get_navigation("anon", node.slug, "auto") is not None

    token = create_access_token(moderator_user.id)
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post(
        "/admin/navigation/cache/invalidate",
        json={"scope": "node", "node_slug": node.slug},
        headers=headers,
    )
    assert resp.status_code == 200
    assert await navcache.get_navigation("anon", node.slug, "auto") is None
