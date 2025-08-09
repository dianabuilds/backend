from __future__ import annotations

import uuid
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select

from app.models.node import Node


class CompassRepository:
    """Repository for fetching similar nodes using pgvector."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_similar_nodes_pgvector(
        self, node: Node, limit: int, probes: int
    ) -> Optional[List[Tuple[Node, float]]]:
        """Return list of (Node, distance) using pgvector kNN.

        If pgvector or PostgreSQL is not available, returns None to allow
        the caller to fallback to a different backend.
        """
        bind = self.session.get_bind()
        if bind.dialect.name != "postgresql":
            return None
        try:
            # Configure search accuracy vs speed
            await self.session.execute(
                text("SET LOCAL ivfflat.probes = :p"), {"p": probes}
            )
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
            # Any error (extension missing, etc.) -> fallback
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
