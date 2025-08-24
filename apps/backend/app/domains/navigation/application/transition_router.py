from __future__ import annotations

import logging
import random
import time
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Deque, List, Optional, Sequence, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from app.domains.nodes.infrastructure.models.node import Node
    from app.domains.users.infrastructure.models.user import User

logger = logging.getLogger(__name__)

from app.core.log_events import no_route, transition_finish, transition_start
from app.core.metrics import record_repeat_rate, record_route_latency_ms


class TransitionProvider(ABC):
    """Interface for objects that return possible transitions from a node."""

    @abstractmethod
    async def get_transitions(
        self,
        db: AsyncSession,
        node: Node,
        user: Optional[User],
        workspace_id: UUID,
    ) -> Sequence[Node]:
        """Return candidate nodes for transition."""


class Policy(ABC):
    """Policy defines how to pick next transition from provider's output."""

    name: str

    def __init__(self, provider: TransitionProvider) -> None:
        self.provider = provider

    @abstractmethod
    async def choose(
        self,
        db: AsyncSession,
        node: Node,
        user: Optional[User],
        history: Deque[str],
    ) -> Tuple[Optional["Node"], "TransitionTrace"]:
        """Return next node and trace info or ``None`` if not applicable."""


class ManualTransitionsProvider(TransitionProvider):
    def __init__(self, service: "TransitionsService" | None = None) -> None:
        if service is None:
            from app.domains.navigation.application.transitions_service import (
                TransitionsService,
            )
            service = TransitionsService()
        self._service = service

    async def get_transitions(
        self,
        db: AsyncSession,
        node: Node,
        user: Optional[User],
        workspace_id: UUID,
    ) -> Sequence[Node]:
        transitions = await self._service.get_transitions(
            db, node, user, workspace_id
        )
        return [t.to_node for t in transitions]


class CompassProvider(TransitionProvider):
    def __init__(self, service: "CompassService" | None = None, limit: int = 5) -> None:
        if service is None:
            from app.domains.navigation.application.compass_service import CompassService

            service = CompassService()
        self._service = service
        self._limit = limit

    async def get_transitions(
        self,
        db: AsyncSession,
        node: Node,
        user: Optional[User],
        workspace_id: UUID,
    ) -> Sequence[Node]:
        nodes = await self._service.get_compass_nodes(db, node, user, self._limit)
        return [n for n in nodes if n.workspace_id == workspace_id]


class RandomProvider(TransitionProvider):
    """Provide random candidates using own RNG for reproducibility."""

    def __init__(self) -> None:
        self._rnd = random.Random()

    def set_seed(self, seed: int | None) -> None:
        self._rnd.seed(seed)

    async def get_transitions(
        self,
        db: AsyncSession,
        node: Node,
        user: Optional[User],
        workspace_id: UUID,
    ) -> Sequence[Node]:
        from app.core.pagination import scope_by_workspace
        from app.domains.navigation.application.access_policy import has_access_async
        from app.domains.nodes.infrastructure.models.node import Node

        query = select(Node).where(
            Node.is_visible == True,  # noqa: E712
            Node.is_public == True,
            Node.is_recommendable == True,
            Node.id != node.id,
            Node.workspace_id == workspace_id,
        )
        query = scope_by_workspace(query, workspace_id)
        result = await db.execute(query)
        nodes: List[Node] = result.scalars().all()
        nodes = [n for n in nodes if await has_access_async(n, user)]
        if not nodes:
            return []
        return [self._rnd.choice(nodes)]


class ManualPolicy(Policy):
    name = "manual"

    async def choose(
        self,
        db: AsyncSession,
        node: Node,
        user: Optional[User],
        history: Deque[str],
    ) -> Tuple[Optional[Node], "TransitionTrace"]:
        candidates = await self.provider.get_transitions(
            db, node, user, node.workspace_id
        )
        candidate_slugs = [n.slug for n in candidates]
        filtered = [n.slug for n in candidates if n.slug in history]
        for n in candidates:
            if n.slug not in history:
                return n, TransitionTrace(candidate_slugs, filtered, {}, n.slug)
        return None, TransitionTrace(candidate_slugs, filtered, {}, None)


class CompassPolicy(Policy):
    name = "compass"

    async def choose(
        self,
        db: AsyncSession,
        node: Node,
        user: Optional[User],
        history: Deque[str],
    ) -> Tuple[Optional[Node], "TransitionTrace"]:
        candidates = await self.provider.get_transitions(
            db, node, user, node.workspace_id
        )
        candidate_slugs = [n.slug for n in candidates]
        filtered = [n.slug for n in candidates if n.slug in history]
        for n in candidates:
            if n.slug not in history:
                return n, TransitionTrace(candidate_slugs, filtered, {}, n.slug)
        return None, TransitionTrace(candidate_slugs, filtered, {}, None)


class RandomPolicy(Policy):
    name = "random"

    def __init__(self, provider: TransitionProvider) -> None:
        super().__init__(provider)
        self._rnd = random.Random()

    def set_seed(self, seed: int | None) -> None:
        self._rnd.seed(seed)
        if hasattr(self.provider, "set_seed"):
            self.provider.set_seed(seed)

    async def choose(
        self,
        db: AsyncSession,
        node: Node,
        user: Optional[User],
        history: Deque[str],
    ) -> Tuple[Optional[Node], "TransitionTrace"]:
        candidates = await self.provider.get_transitions(
            db, node, user, node.workspace_id
        )
        candidate_slugs = [n.slug for n in candidates]
        filtered = [n.slug for n in candidates if n.slug in history]
        candidates = [n for n in candidates if n.slug not in history]
        if not candidates:
            return None, TransitionTrace(candidate_slugs, filtered, {}, None)
        chosen = self._rnd.choice(candidates)
        return chosen, TransitionTrace(candidate_slugs, filtered, {}, chosen.slug)


@dataclass
class TransitionTrace:
    candidates: List[str]
    filters: List[str]
    scores: dict
    chosen: Optional[str]


class NoRouteReason(Enum):
    NO_ROUTE = "NO_ROUTE"
    TIMEOUT = "timeout"
    BUDGET_EXCEEDED = "budget_exceeded"


@dataclass
class TransitionResult:
    next: Optional["Node"]
    reason: Optional[NoRouteReason]
    trace: List[TransitionTrace]
    metrics: dict


class TransitionRouter:
    """Routes transitions according to provided policies."""

    def __init__(self, policies: Sequence[Policy], not_repeat_last: int = 0) -> None:
        self.policies = list(policies)
        self.history: Deque[str] = deque(maxlen=not_repeat_last)
        self.trace: List[TransitionTrace] = []

    async def _next(
        self, db: AsyncSession, node: Node, user: Optional[User]
    ) -> Optional[Node]:
        for policy in self.policies:
            candidate, trace = await policy.choose(db, node, user, self.history)
            self.trace.append(trace)
            if candidate and candidate.slug not in self.history:
                self.history.append(candidate.slug)
                logger.debug("%s -> %s", policy.name, candidate.slug)
                return candidate
        return None

    async def route(
        self,
        db: AsyncSession,
        start: Node,
        user: Optional[User],
        budget,
        seed: int | None = None,
    ) -> TransitionResult:
        transition_start(start.slug)
        start_time = time.monotonic()
        self.trace.clear()
        if seed is not None:
            for policy in self.policies:
                if hasattr(policy, "set_seed"):
                    policy.set_seed(seed)
                if hasattr(policy.provider, "set_seed"):
                    policy.provider.set_seed(seed)

        self.history.append(start.slug)
        nxt = await self._next(db, start, user)

        elapsed_ms = (time.monotonic() - start_time) * 1000
        total_candidates = sum(len(t.candidates) for t in self.trace)
        filtered = sum(len(t.filters) for t in self.trace)
        repeat_rate = filtered / total_candidates if total_candidates else 0.0
        metrics = {
            "elapsed_ms": elapsed_ms,
            "db_queries": 0,
            "repeat_rate": repeat_rate,
        }
        record_route_latency_ms(elapsed_ms)
        record_repeat_rate(repeat_rate)

        reason: Optional[NoRouteReason] = None
        if elapsed_ms > getattr(budget, "time_ms", float("inf")):
            reason = NoRouteReason.TIMEOUT
        elif metrics["db_queries"] > getattr(budget, "db_queries", float("inf")):
            reason = NoRouteReason.BUDGET_EXCEEDED
        elif nxt is None:
            reason = NoRouteReason.NO_ROUTE
            no_route(start.slug)

        transition_finish(nxt.slug if nxt else None)
        return TransitionResult(next=nxt, reason=reason, trace=list(self.trace), metrics=metrics)
