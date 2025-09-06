from __future__ import annotations

import logging
from collections import defaultdict, deque
from dataclasses import asdict
from datetime import datetime
from types import SimpleNamespace

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps.guards import check_transition
from app.core.preview import PreviewContext
from app.domains.navigation.application.access_policy import has_access_async
from app.domains.navigation.infrastructure.cache_adapter import CoreCacheAdapter
from app.domains.navigation.infrastructure.history_store import RedisHistoryStore
from app.domains.nodes.infrastructure.models.node import Node
from app.domains.quests.infrastructure.models.navigation_cache_models import (
    NavigationCache,
)
from app.domains.users.infrastructure.models.user import User

from .policies import (
    CompassPolicy,
    EchoPolicy,
    FallbackPolicy,
    ManualPolicy,
    RandomPolicy,
)
from .ports.history_port import IUserHistoryStore
from .providers import (
    CompassProvider,
    EchoProvider,
    ManualTransitionsProvider,
    RandomProvider,
)
from .router import TransitionResult, TransitionRouter

logger = logging.getLogger(__name__)


class NavigationService:
    def __init__(self, history_store: IUserHistoryStore | None = None) -> None:
        policies = [
            ManualPolicy(ManualTransitionsProvider()),
            EchoPolicy(EchoProvider()),
            CompassPolicy(CompassProvider()),
            RandomPolicy(RandomProvider()),
            FallbackPolicy(),
        ]
        self._router = TransitionRouter(
            policies,
            not_repeat_last=5,
            no_repeat_window=50,
            repeat_threshold=0.5,
            repeat_decay=0.8,
            max_visits=5,
        )
        self._history_store = history_store or RedisHistoryStore(CoreCacheAdapter(), 50)

    async def build_route(
        self,
        db: AsyncSession,
        node: Node,
        user: User | None,
        preview: PreviewContext | None = None,
        *,
        mode: str | None = None,
    ) -> TransitionResult:
        budget = SimpleNamespace(
            max_time_ms=1000,
            max_queries=1000,
            max_filters=1000,
            fallback_chain=[],
        )
        if user and self._history_store:
            tags, slugs = await self._history_store.load(user.id)
            self._router.history = deque(slugs, maxlen=self._router.history.maxlen)
            rf = self._router.repeat_filter
            rf.tag_history = deque(tags, maxlen=rf.window)
            rf.tag_counts = defaultdict(int)
            for t in tags:
                rf.tag_counts[t] += 1
            rf.visit_counts = defaultdict(int)
            for s in slugs:
                rf.visit_counts[s] += 1
        result = await self._router.route(
            db,
            node,
            user,
            budget,
            mode=mode,
            preview=preview,
        )
        if user and self._history_store:
            await self._history_store.save(
                user.id,
                list(self._router.repeat_filter.tag_history),
                list(self._router.history),
            )
        return result

    async def get_next(
        self,
        db: AsyncSession,
        node: Node,
        user: User | None,
        preview: PreviewContext | None = None,
        *,
        mode: str | None = None,
    ) -> TransitionResult:
        res = await self.build_route(db, node, user, preview=preview, mode=mode)
        logger.info("navigation.trace", extra={"trace": [asdict(t) for t in res.trace]})
        return res

    async def _filter_transitions(
        self,
        db: AsyncSession,
        transitions: list[dict[str, object]],
        user: User | None,
        preview: PreviewContext | None,
    ) -> list[dict[str, object]]:
        """Apply access checks to cached transitions."""
        allowed: list[dict[str, object]] = []
        for t in transitions:
            slug = t.get("slug")
            if not slug:
                continue
            result = await db.execute(select(Node).where(Node.slug == slug))
            node = result.scalars().first()
            if not node:
                continue
            if not await has_access_async(node, user, preview):
                continue
            transition = SimpleNamespace(
                id=t.get("id") or slug,
                condition=t.get("condition"),
            )
            if await check_transition(transition, user, preview):
                allowed.append(t)
        return allowed

    async def generate_transitions(
        self,
        db: AsyncSession,
        node: Node,
        user: User | None,
        preview: PreviewContext | None = None,
    ) -> list[dict[str, object]]:
        stmt = select(NavigationCache.navigation).where(NavigationCache.node_slug == node.slug)
        if FeatureFlagKey.NAV_CACHE_V2.value in flags and account_id is not None:
            stmt = stmt.where(NavigationCache.account_id == account_id)
        result = await db.execute(stmt)
        data = result.scalar_one_or_none()
        if not data:
            return []
        transitions: list[dict[str, object]] = data.get("transitions", [])
        return await self._filter_transitions(db, transitions, user, preview)

    async def get_navigation(
        self,
        db: AsyncSession,
        node: Node,
        user: User | None,
        preview: PreviewContext | None = None,
    ) -> dict[str, object]:
        stmt = select(NavigationCache.navigation).where(NavigationCache.node_slug == node.slug)
        if FeatureFlagKey.NAV_CACHE_V2.value in flags and account_id is not None:
            stmt = stmt.where(NavigationCache.account_id == account_id)
        result = await db.execute(stmt)
        data = result.scalar_one_or_none()
        if data:
            transitions: list[dict[str, object]] = data.get("transitions", [])
            data["transitions"] = await self._filter_transitions(db, transitions, user, preview)
            return data
        return {
            "mode": "auto",
            "transitions": [],
            "generated_at": (
                preview.now if preview and preview.now else datetime.utcnow()
            ).isoformat(),
        }

    async def invalidate_navigation_cache(self, db: AsyncSession, node: Node) -> None:
        stmt = delete(NavigationCache).where(NavigationCache.node_slug == node.slug)
        if FeatureFlagKey.NAV_CACHE_V2.value in flags and account_id is not None:
            stmt = stmt.where(NavigationCache.account_id == account_id)
        await db.execute(stmt)
        await db.flush()
