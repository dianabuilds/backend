from __future__ import annotations

import random
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.preview import PreviewContext
from app.domains.ai.application.embedding_service import (
    cosine_similarity,
    update_node_embedding,
)
from app.domains.navigation.application.access_policy import has_access_async
from app.domains.navigation.application.navigation_cache_service import (
    NavigationCacheService,
)
from app.domains.navigation.infrastructure.cache_adapter import CoreCacheAdapter
from app.domains.navigation.infrastructure.models.echo_models import EchoTrace
from app.domains.navigation.infrastructure.repositories.compass_repository import (
    CompassRepository,
)
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.users.infrastructure.models.user import User
from app.domains.workspaces.limits import workspace_limit


class CompassService:
    def __init__(self) -> None:
        self._navcache = NavigationCacheService(CoreCacheAdapter())

    @workspace_limit("compass_calls", scope="day", amount=1)
    async def get_compass_nodes(
        self,
        db: AsyncSession,
        node: Node,
        user: User | None,
        limit: int = 5,
        preview: PreviewContext | None = None,
    ) -> list[Node]:
        if preview and preview.seed is not None:
            random.seed(preview.seed)
        if not node.is_recommendable:
            return []
        if not node.embedding_vector:
            await update_node_embedding(db, node)

        user_key = str(user.id) if user else "anon"
        params_hash = f"{node.id}:{limit}"
        if settings.cache.enable_compass_cache:
            cached = await self._navcache.get_compass(user_key, params_hash)
            if cached:
                ids = cached.get("ids", [])
                nodes: list[Node] = []
                for node_id in ids:
                    n = await db.get(Node, uuid.UUID(node_id))
                    if not n or not await has_access_async(n, user, preview):
                        continue
                    nodes.append(n)
                return nodes

        repo = CompassRepository(db)
        candidates_with_dist: list[tuple[Node, float]] | None = (
            await repo.get_similar_nodes_pgvector(
                node,
                settings.compass.top_k_db,
                settings.compass.pgv_probes,
            )
        )

        if candidates_with_dist is None:
            query = select(Node).where(
                Node.id != node.id,
                Node.is_visible.is_(True),
                Node.is_public.is_(True),
                Node.is_recommendable.is_(True),
                Node.embedding_vector.isnot(None),
            )
            result = await db.execute(query)
            nodes = result.scalars().all()
            candidates_with_dist = []
            for cand in nodes:
                if not cand.embedding_vector:
                    continue
                dist = 1 - cosine_similarity(
                    node.embedding_vector, cand.embedding_vector
                )
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
            if not await has_access_async(cand, user, preview):
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
        limit = min(limit, settings.compass.top_k_result)
        selected = [c for c, _, _, _ in scored[:limit]]

        if surprises:
            surprise_node = random.choice(surprises)
            if surprise_node not in selected:
                pos = random.randint(0, len(selected))
                selected.insert(pos, surprise_node)
                if len(selected) > limit:
                    selected = selected[:limit]

        if settings.cache.enable_compass_cache:
            await self._navcache.set_compass(
                user_key,
                params_hash,
                {"ids": [str(n.id) for n in selected]},
                settings.cache.compass_cache_ttl,
            )
        return selected
