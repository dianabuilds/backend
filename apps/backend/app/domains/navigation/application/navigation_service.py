from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.preview import PreviewContext
from app.domains.navigation.application.access_policy import has_access_async
from app.domains.navigation.application.compass_service import CompassService
from app.domains.navigation.application.echo_service import EchoService
from app.domains.navigation.application.navigation_cache_service import (
    NavigationCacheService,
)
from app.domains.navigation.application.random_service import RandomService
from app.domains.navigation.application.transition_router import (
    CompassPolicy,
    CompassProvider,
    ManualPolicy,
    ManualTransitionsProvider,
    RandomPolicy,
    RandomProvider,
    TransitionRouter,
)
from app.domains.navigation.application.transitions_service import TransitionsService
from app.domains.navigation.infrastructure.cache_adapter import CoreCacheAdapter
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.users.infrastructure.models.user import User

logger = logging.getLogger(__name__)


def _normalise(scores: List[Node]) -> dict[str, float]:
    if not scores:
        return {}
    size = len(scores)
    return {n.slug: 1 - i / size for i, n in enumerate(scores)}


class NavigationService:
    def __init__(self) -> None:
        self._echo = EchoService()
        self._compass = CompassService()
        self._navcache = NavigationCacheService(CoreCacheAdapter())
        manual_provider = ManualTransitionsProvider(TransitionsService())
        compass_provider = CompassProvider(self._compass)
        random_provider = RandomProvider()
        self._router = TransitionRouter(
            [
                ManualPolicy(manual_provider),
                CompassPolicy(compass_provider),
                RandomPolicy(random_provider),
            ],
            not_repeat_last=settings.navigation.no_repeat_last_n,
        )

    async def generate_transitions(
        self, db: AsyncSession, node: Node, user: Optional[User]
    ) -> List[Dict[str, object]]:
        max_options = settings.navigation.max_options

        manual: List[Dict[str, object]] = []
        for t in await TransitionsService().get_transitions(
            db, node, user, node.workspace_id
        ):
            if not await has_access_async(t.to_node, user):
                continue
            manual.append(
                {
                    "slug": t.to_node.slug,
                    "title": t.to_node.title,
                    "source_type": t.type.value,
                    "score": float(t.weight or 1),
                }
            )

        manual.sort(key=lambda x: (-x["score"], x["slug"]))

        remaining = max_options - len(manual)
        if remaining <= 0:
            return manual

        compass_nodes = await self._compass.get_compass_nodes(db, node, user, remaining)
        echo_nodes = await self._echo.get_echo_transitions(
            db, node, remaining, user=user
        )
        rnd = await RandomService().get_random_node(
            db, user=user, exclude_node_id=str(node.id)
        )

        candidates: dict[str, dict[str, object]] = {}

        for source, nodes in {
            "compass": compass_nodes,
            "echo": echo_nodes,
        }.items():
            norm = _normalise(nodes)
            for n in nodes:
                if not await has_access_async(n, user):
                    continue
                data = candidates.setdefault(
                    n.slug, {"node": n, "scores": defaultdict(float)}
                )
                data["scores"][source] = norm[n.slug]

        if rnd and await has_access_async(rnd, user):
            data = candidates.setdefault(
                rnd.slug, {"node": rnd, "scores": defaultdict(float)}
            )
            data["scores"]["random"] = 1.0

        weighted: List[Dict[str, object]] = []
        for slug, data in candidates.items():
            n: Node = data["node"]
            s = data["scores"]
            total = (
                settings.navigation.weight_compass * s.get("compass", 0)
                + settings.navigation.weight_echo * s.get("echo", 0)
                + settings.navigation.weight_random * s.get("random", 0)
            )
            source_type = max(s.items(), key=lambda kv: kv[1])[0]
            weighted.append(
                {
                    "slug": slug,
                    "title": n.title,
                    "source_type": source_type,
                    "score": round(float(total), 4),
                }
            )

        weighted.sort(key=lambda x: (-x["score"], x["slug"]))
        seen = {t["slug"] for t in manual}
        automatic = [t for t in weighted if t["slug"] not in seen][: max(0, remaining)]
        return manual + automatic

    async def build_route(
        self,
        db: AsyncSession,
        node: Node,
        user: Optional[User],
        steps: int,
        preview: PreviewContext | None = None,
    ) -> List[Node]:
        from types import SimpleNamespace

        route: List[Node] = [node]
        current = node
        budget = SimpleNamespace(
            max_time_ms=1000, max_queries=1000, max_filters=1000, fallback_chain=[]
        )
        for _ in range(steps):
            result = await self._router.route(
                db, current, user, budget, seed=0, preview=preview
            )
            logger.debug("trace: %s", result.trace)
            if result.next is None:
                break
            current = result.next
            route.append(current)
        return route

    async def get_navigation(
        self, db: AsyncSession, node: Node, user: Optional[User]
    ) -> Dict[str, object]:
        user_key = str(user.id) if user else "anon"
        if settings.cache.enable_nav_cache:
            cached = await self._navcache.get_navigation(user_key, node.slug, "auto")
            if cached:
                return cached
        transitions = await self.generate_transitions(db, node, user)
        data = {
            "mode": "auto",
            "transitions": transitions,
            "generated_at": datetime.utcnow().isoformat(),
        }
        if settings.cache.enable_nav_cache:
            await self._navcache.set_navigation(
                user_key,
                node.slug,
                "auto",
                data,
                settings.cache.nav_cache_ttl,
            )
        return data

    async def invalidate_navigation_cache(
        self, user: Optional[User], node: Node
    ) -> None:
        await self._navcache.invalidate_navigation_by_node(node.slug)

    async def invalidate_all_for_node(self, node: Node) -> None:
        await self._navcache.invalidate_navigation_by_node(node.slug)
