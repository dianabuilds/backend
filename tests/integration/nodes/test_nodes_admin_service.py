import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.application.services.nodes_admin_service import NodesAdminService
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.nodes.infrastructure.repositories.node_repository import (
    NodeRepositoryAdapter,
)


@pytest.mark.asyncio
async def test_bulk_visibility_and_public_and_tags(db_session: AsyncSession, test_user):
    n1 = Node(
        title="N1",
        content={},
        author_id=test_user.id,
        is_public=False,
        is_visible=False,
    )
    n2 = Node(
        title="N2",
        content={},
        author_id=test_user.id,
        is_public=False,
        is_visible=False,
    )
    db_session.add_all([n1, n2])
    await db_session.commit()
    await db_session.refresh(n1)
    await db_session.refresh(n2)

    svc = NodesAdminService(NodeRepositoryAdapter(db_session))

    # bulk visibility
    c_vis = await svc.bulk_set_visibility(db_session, [n1.id, n2.id], True)
    assert c_vis == 2
    await db_session.refresh(n1)
    await db_session.refresh(n2)
    assert n1.is_visible and n2.is_visible

    # bulk public
    c_pub = await svc.bulk_set_public(db_session, [n1.id, n2.id], True)
    assert c_pub == 2
    await db_session.refresh(n1)
    await db_session.refresh(n2)
    assert n1.is_public and n2.is_public

    # bulk set tags
    c_tags = await svc.bulk_set_tags(db_session, [n1.id, n2.id], ["a", "b"])
    assert c_tags == 2

    # bulk set tags diff (add c, remove a)
    c_diff = await svc.bulk_set_tags_diff(db_session, [n1.id, n2.id], ["c"], ["a"])
    assert c_diff == 2
