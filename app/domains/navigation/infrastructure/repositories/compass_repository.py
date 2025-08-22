from __future__ import annotations

import uuid
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select

from app.domains.nodes.infrastructure.models.node import Node


class CompassRepository:
    """Repository for fetching similar nodes using pgvector."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_similar_nodes_pgvector(
        self, node: Node, limit: int, probes: int
    ) -> Optional[List[Tuple[Node, float]]]:
        bind = self.session.get_bind()
        if bind.dialect.name != "postgresql":
            return None
        try:
            await self.session.execute(text("SET LOCAL ivfflat.probes = :p"), {"p": probes})
            query = text(
                """
                SELECT id, embedding_vector <=> :vec AS dist
                FROM nodes
                WHERE is_visible = true
                  AND is_public = true
                  AND is_recommendable = true
                  AND embedding_vector IS NOT NULL
                  AND id <> :id
                ORDER BY embedding_vector <=> :vec
                LIMIT :limit
                """
            )
            rows = await self.session.execute(
                query,
                {"vec": node.embedding_vector, "id": str(node.id), "limit": limit},
            )
            mappings = rows.mappings().all()
        except Exception:
            return None
        if not mappings:
            return []
        ids: List[uuid.UUID] = []
        dists: dict[uuid.UUID, float] = {}
        for m in mappings:
            uid = uuid.UUID(m["id"])
            ids.append(uid)
            dists[uid] = float(m["dist"])
        result = await self.session.execute(select(Node).where(Node.id.in_(ids)))
        node_map = {n.id: n for n in result.scalars().all()}
        return [(node_map[i], dists[i]) for i in ids if i in node_map]

    async def search_by_vector_pgvector(
        self, query_vec: List[float], limit: int, probes: int
    ) -> Optional[List[Tuple[Node, float]]]:
        bind = self.session.get_bind()
        if bind.dialect.name != "postgresql":
            return None
        try:
            await self.session.execute(text("SET LOCAL ivfflat.probes = :p"), {"p": probes})
            query = text(
                """
                SELECT id, embedding_vector <=> :vec AS dist
                FROM nodes
                WHERE is_visible = true
                  AND is_public = true
                  AND is_recommendable = true
                  AND embedding_vector IS NOT NULL
                ORDER BY embedding_vector <=> :vec
                LIMIT :limit
                """
            )
            rows = await self.session.execute(query, {"vec": query_vec, "limit": limit})
            mappings = rows.mappings().all()
        except Exception:
            return None
        if not mappings:
            return []
        ids: List[uuid.UUID] = []
        dists: dict[uuid.UUID, float] = {}
        for m in mappings:
            uid = uuid.UUID(m["id"])
            ids.append(uid)
            dists[uid] = float(m["dist"])
        result = await self.session.execute(select(Node).where(Node.id.in_(ids)))
        node_map = {n.id: n for n in result.scalars().all()}
        return [(node_map[i], dists[i]) for i in ids if i in node_map]
