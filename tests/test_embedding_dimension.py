import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import create_access_token
from app.engine.embedding import (
    register_embedding_provider,
    simple_embedding,
    EMBEDDING_DIM,
)
from app.domains.nodes.infrastructure.models.node import Node


@pytest.mark.asyncio
async def test_node_creation_handles_provider_dim(
    client: AsyncClient, db_session: AsyncSession, test_user
):
    token = create_access_token(test_user.id)

    def fake_provider(text: str):
        # Return a vector with a dimension different from the DB schema
        return [0.1] * (EMBEDDING_DIM + 10)

    # Register mismatched provider
    register_embedding_provider(fake_provider, EMBEDDING_DIM + 10)

    payload = {
        "title": "dim test",
        "nodes": {"time": 0, "blocks": [], "version": "2"},
    }
    resp = await client.post(
        "/nodes",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    slug = resp.json()["slug"]

    result = await db_session.execute(select(Node).where(Node.slug == slug))
    node = result.scalars().first()
    assert node is not None
    assert node.embedding_vector is not None
    assert len(node.embedding_vector) == EMBEDDING_DIM

    # Restore default provider to avoid side effects on other tests
    register_embedding_provider(simple_embedding, EMBEDDING_DIM)
