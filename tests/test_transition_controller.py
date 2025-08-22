import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.nodes.infrastructure.models.node import Node
from app.domains.navigation.infrastructure.models.transition_models import NodeTransition, NodeTransitionType
from app.domains.ai.application.embedding_service import update_node_embedding
from app.domains.tags.application.tag_helpers import get_or_create_tags


@pytest.mark.asyncio
async def test_next_modes_and_max_options(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user,
    auth_headers,
):
    controller = {
        "type": "transition_controller",
        "max_options": 3,
        "default_mode": "compass",
        "modes": [
            {
                "mode": "compass",
                "label": "Поверить компасу",
                "filters": {"tag_similarity": True},
            },
            {"mode": "random", "label": "Random", "filters": {}}
        ],
    }
    base = Node(
        title="base",
        content={},
        is_public=True,
        author_id=test_user.id,
        meta={"transition_controller": controller},
    )
    base.tags = await get_or_create_tags(db_session, ["a", "b"])
    db_session.add(base)
    targets = []
    tags_list = [["a", "b"], ["a"], ["b"], ["c"], ["d"]]
    for i, tags in enumerate(tags_list):
        n = Node(
            title=f"n{i}",
            content={},
            is_public=True,
            author_id=test_user.id,
        )
        n.tags = await get_or_create_tags(db_session, tags)
        db_session.add(n)
        targets.append(n)
    await db_session.commit()
    for n in [base, *targets]:
        await db_session.refresh(n)
        await update_node_embedding(db_session, n)
    for n in targets:
        tr = NodeTransition(
            from_node_id=base.id,
            to_node_id=n.id,
            type=NodeTransitionType.manual,
            condition={},
            weight=1,
            label=n.title,
            created_by=test_user.id,
        )
        db_session.add(tr)
    await db_session.commit()

    resp = await client.get(f"/nodes/{base.slug}/next_modes", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["default_mode"] == "compass"
    assert any(m["mode"] == "compass" for m in data["modes"])

    resp = await client.get(
        f"/nodes/{base.slug}/next?mode=compass", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "compass"
    assert len(data["transitions"]) == 3
