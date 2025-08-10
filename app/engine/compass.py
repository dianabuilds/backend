from __future__ import annotations

import random
import uuid
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.models.echo_trace import EchoTrace
from app.models.node import Node
from app.models.user import User
from app.repositories.compass_repository import CompassRepository
from app.services.compass_cache import compass_cache
from .embedding import cosine_similarity, update_node_embedding
from .filters import has_access_async


async def get_compass_nodes(
    db: AsyncSession, node: Node, user: User | None, limit: int = 5
) -> List[Node]:
    """Return nodes similar to the given node using embeddings and tags."""
    if not node.is_recommendable:
        return []
    if not node.embedding_vector:
        await update_node_embedding(db, node)

    user_key = str(user.id) if user else None
    cached = await compass_cache.get(user_key, str(node.id))
    if cached:
        nodes: List[Node] = []
        for node_id in cached:
            n = await db.get(Node, uuid.UUID(node_id))
            if not n or not await has_access_async(n, user):
                continue
            nodes.append(n)
        return nodes

    repo = CompassRepository(db)
    candidates_with_dist: Optional[List[Tuple[Node, float]]] = await repo.get_similar_nodes_pgvector(
        node,
        settings.compass_top_k_db,
        settings.compass_pgv_probes,
    )

    if candidates_with_dist is None:
        query = select(Node).where(
            Node.id != node.id,
            Node.is_visible == True,
            Node.is_public == True,
            Node.is_recommendable == True,
            Node.embedding_vector.isnot(None),
        )
        result = await db.execute(query)
        nodes = result.scalars().all()
        candidates_with_dist = []
        for cand in nodes:
            if not cand.embedding_vector:
                continue
            dist = 1 - cosine_similarity(node.embedding_vector, cand.embedding_vector)
            candidates_with_dist.append((cand, dist))

    visited: set[uuid.UUID] = set()
    if user:
        res = await db.execute(
            select(EchoTrace.to_node_id).where(EchoTrace.user_id == user.id)
        )
        visited = {r for r in res.scalars().all()}

    scored: list[tuple[Node, float, float, int]] = []
    surprises: list[Node] = []
    node_tags = set(node.tag_slugs)
    for cand, dist in candidates_with_dist:
        if cand.id in visited:
            continue
        if not await has_access_async(cand, user):
            continue
        if not cand.embedding_vector:
            continue
        sim = 1 - dist
        tag_match = len(node_tags & set(cand.tag_slugs))
        rarity = 1 / (1 + (cand.popularity_score or 0))
        deviation_boost = random.uniform(0.9, 1.1)
        score = (sim * 0.5 + tag_match * 0.2 + rarity * 0.3) * deviation_boost
        scored.append((cand, score, sim, tag_match))
        if tag_match > 0 and sim < 0.3:
            surprises.append(cand)

    scored.sort(key=lambda x: x[1], reverse=True)
    limit = min(limit, settings.compass_top_k_result)
    selected = [c for c, _, _, _ in scored[:limit]]

    if surprises:
        surprise_node = random.choice(surprises)
        if surprise_node not in selected:
            pos = random.randint(0, len(selected))
            selected.insert(pos, surprise_node)
            if len(selected) > limit:
                selected = selected[:limit]

    await compass_cache.set(user_key, str(node.id), [str(n.id) for n in selected])
    return selected
