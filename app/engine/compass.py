from __future__ import annotations

from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.node import Node
from app.models.user import User
from .embedding import cosine_similarity, update_node_embedding


async def get_compass_nodes(
    db: AsyncSession, node: Node, user: User, limit: int = 3
) -> List[Node]:
    """Return nodes similar to the given node using embeddings and tags."""
    if not node.embedding_vector:
        await update_node_embedding(db, node)

    query = select(Node).where(
        Node.id != node.id, Node.is_visible == True, Node.is_public == True
    )
    result = await db.execute(query)
    candidates = result.scalars().all()

    def score(other: Node) -> float:
        if not other.embedding_vector:
            return -1
        sim = cosine_similarity(node.embedding_vector, other.embedding_vector)
        tag_bonus = len(set(node.tags or []) & set(other.tags or []))
        return sim + tag_bonus

    filtered = []
    for n in candidates:
        if n.premium_only and not user.is_premium:
            continue
        filtered.append(n)

    filtered.sort(key=score, reverse=True)
    return filtered[:limit]
