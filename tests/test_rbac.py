"""Tests for RBAC helpers and permissions."""
import logging
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.node import Node
from app.models.transition import NodeTransition, NodeTransitionType
from app.models.user import User


async def _create_node(db: AsyncSession, author: User) -> Node:
    node = Node(
        title="n",
        content_format="markdown",
        content={},
        author_id=author.id,
        is_public=True,
    )
    db.add(node)
    await db.commit()
    await db.refresh(node)
    return node


async def _create_transition(
    db: AsyncSession, from_node: Node, to_node: Node, creator: User
) -> NodeTransition:
    tr = NodeTransition(
        from_node_id=from_node.id,
        to_node_id=to_node.id,
        type=NodeTransitionType.manual,
        created_by=creator.id,
    )
    db.add(tr)
    await db.commit()
    await db.refresh(tr)
    return tr


# --- Role change -----------------------------------------------------------


@pytest.mark.asyncio
async def test_admin_cannot_change_self_role(
    client: AsyncClient, admin_user: User
):
    token = create_access_token(admin_user.id)
    resp = await client.post(
        f"/admin/users/{admin_user.id}/role",
        json={"role": "user"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_moderator_cannot_change_role(
    client: AsyncClient, moderator_user: User, test_user: User
):
    token = create_access_token(moderator_user.id)
    resp = await client.post(
        f"/admin/users/{test_user.id}/role",
        json={"role": "moderator"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_changes_role_of_lower_user(
    client: AsyncClient, db_session: AsyncSession, admin_user: User, test_user: User, caplog
):
    token = create_access_token(admin_user.id)
    with caplog.at_level(logging.INFO):
        resp = await client.post(
            f"/admin/users/{test_user.id}/role",
            json={"role": "moderator"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200
    await db_session.refresh(test_user)
    assert test_user.role == "moderator"
    assert any(getattr(rec, "action", None) == "set_role" for rec in caplog.records)


@pytest.mark.asyncio
async def test_admin_cannot_change_role_of_admin(
    client: AsyncClient, db_session: AsyncSession, admin_user: User
):
    other_admin = User(
        email="other_admin@example.com",
        username="other_admin",
        password_hash=admin_user.password_hash,
        is_active=True,
        role="admin",
    )
    db_session.add(other_admin)
    await db_session.commit()
    await db_session.refresh(other_admin)
    token = create_access_token(admin_user.id)
    resp = await client.post(
        f"/admin/users/{other_admin.id}/role",
        json={"role": "user"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


# --- Moderation: bans and restrictions -------------------------------------


@pytest.mark.asyncio
async def test_moderator_bans_user(
    client: AsyncClient, moderator_user: User, test_user: User, caplog
):
    token = create_access_token(moderator_user.id)
    with caplog.at_level(logging.INFO):
        resp = await client.post(
            f"/moderation/users/{test_user.id}/ban",
            json={"reason": "spam"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200
    assert any(getattr(rec, "action", None) == "ban_user" for rec in caplog.records)


@pytest.mark.asyncio
async def test_moderator_cannot_ban_admin(
    client: AsyncClient, moderator_user: User, admin_user: User
):
    token = create_access_token(moderator_user.id)
    resp = await client.post(
        f"/moderation/users/{admin_user.id}/ban",
        json={"reason": "spam"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_post_restricted_user_cannot_post(
    client: AsyncClient,
    db_session: AsyncSession,
    moderator_user: User,
    test_user: User,
):
    mod_token = create_access_token(moderator_user.id)
    resp = await client.post(
        f"/moderation/users/{test_user.id}/restrict-posting",
        json={"reason": "bad"},
        headers={"Authorization": f"Bearer {mod_token}"},
    )
    assert resp.status_code == 200

    user_token = create_access_token(test_user.id)
    resp = await client.post(
        "/nodes",
        json={"title": "t", "content_format": "markdown", "content": {}},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 403


# --- Moderation of content -------------------------------------------------


@pytest.mark.asyncio
async def test_moderator_hides_user_node(
    client: AsyncClient,
    db_session: AsyncSession,
    moderator_user: User,
    test_user: User,
):
    node = await _create_node(db_session, test_user)
    token = create_access_token(moderator_user.id)
    resp = await client.post(
        f"/moderation/nodes/{node.slug}/hide",
        json={"reason": "bad"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_moderator_cannot_hide_admin_node(
    client: AsyncClient,
    db_session: AsyncSession,
    moderator_user: User,
    admin_user: User,
):
    node = await _create_node(db_session, admin_user)
    token = create_access_token(moderator_user.id)
    resp = await client.post(
        f"/moderation/nodes/{node.slug}/hide",
        json={"reason": "bad"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


# --- Owner vs role helpers -------------------------------------------------


@pytest.mark.asyncio
async def test_owner_deletes_own_transition(
    client: AsyncClient, db_session: AsyncSession, test_user: User
):
    from_node = await _create_node(db_session, test_user)
    to_node = await _create_node(db_session, test_user)
    transition = await _create_transition(db_session, from_node, to_node, test_user)
    token = create_access_token(test_user.id)
    resp = await client.delete(
        f"/transitions/{transition.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_non_owner_without_rights_cannot_delete_transition(
    client: AsyncClient, db_session: AsyncSession, test_user: User
):
    from_node = await _create_node(db_session, test_user)
    to_node = await _create_node(db_session, test_user)
    transition = await _create_transition(db_session, from_node, to_node, test_user)
    other_user = User(
        email="other@example.com",
        username="other",
        password_hash=test_user.password_hash,
        is_active=True,
        role="user",
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)
    token = create_access_token(other_user.id)
    resp = await client.delete(
        f"/transitions/{transition.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_moderator_deletes_foreign_transition(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user: User,
    moderator_user: User,
):
    from_node = await _create_node(db_session, test_user)
    to_node = await _create_node(db_session, test_user)
    transition = await _create_transition(db_session, from_node, to_node, test_user)
    token = create_access_token(moderator_user.id)
    resp = await client.delete(
        f"/transitions/{transition.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

