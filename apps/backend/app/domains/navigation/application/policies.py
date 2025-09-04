from __future__ import annotations

import random
from abc import ABC, abstractmethod
from collections import deque
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.preview import PreviewContext  # isort: skip

from .providers import TransitionProvider

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from app.domains.nodes.infrastructure.models.node import Node
    from app.domains.users.infrastructure.models.user import User

    from .router import RepeatFilter, TransitionTrace


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
        user: User | None,
        history: deque[str],
        repeat_filter: RepeatFilter,
        preview: PreviewContext | None = None,
    ) -> tuple[Node | None, TransitionTrace]:
        """Return next node and trace info or ``None`` if not applicable."""


class ManualPolicy(Policy):
    name = "manual"

    async def choose(
        self,
        db: AsyncSession,
        node: Node,
        user: User | None,
        history: deque[str],
        repeat_filter: RepeatFilter,
        preview: PreviewContext | None = None,
    ) -> tuple[Node | None, TransitionTrace]:
        try:
            candidates = await self.provider.get_transitions(
                db, node, user, node.workspace_id, preview=preview
            )
        except TypeError:
            candidates = await self.provider.get_transitions(
                db, node, user, node.workspace_id
            )
        candidate_slugs = [n.slug for n in candidates]
        filtered = [n.slug for n in candidates if n.slug in history]
        candidates = [n for n in candidates if n.slug not in history]
        candidates, filt2 = repeat_filter.filter(candidates)
        filtered.extend(filt2)
        from .router import TransitionTrace

        for n in candidates:
            return n, TransitionTrace(candidate_slugs, filtered, {}, n.slug)
        return None, TransitionTrace(candidate_slugs, filtered, {}, None)


class CompassPolicy(Policy):
    name = "compass"

    async def choose(
        self,
        db: AsyncSession,
        node: Node,
        user: User | None,
        history: deque[str],
        repeat_filter: RepeatFilter,
        preview: PreviewContext | None = None,
    ) -> tuple[Node | None, TransitionTrace]:
        try:
            candidates = await self.provider.get_transitions(
                db, node, user, node.workspace_id, preview=preview
            )
        except TypeError:
            candidates = await self.provider.get_transitions(
                db, node, user, node.workspace_id
            )
        candidate_slugs = [n.slug for n in candidates]
        filtered = [n.slug for n in candidates if n.slug in history]
        candidates = [n for n in candidates if n.slug not in history]
        candidates, filt2 = repeat_filter.filter(candidates)
        filtered.extend(filt2)
        from .router import TransitionTrace

        for n in candidates:
            return n, TransitionTrace(candidate_slugs, filtered, {}, n.slug)
        return None, TransitionTrace(candidate_slugs, filtered, {}, None)


class EchoPolicy(Policy):
    name = "echo"

    async def choose(
        self,
        db: AsyncSession,
        node: Node,
        user: User | None,
        history: deque[str],
        repeat_filter: RepeatFilter,
        preview: PreviewContext | None = None,
    ) -> tuple[Node | None, TransitionTrace]:
        try:
            candidates = await self.provider.get_transitions(
                db, node, user, node.workspace_id, preview=preview
            )
        except TypeError:
            candidates = await self.provider.get_transitions(
                db, node, user, node.workspace_id
            )
        candidate_slugs = [n.slug for n in candidates]
        filtered = [n.slug for n in candidates if n.slug in history]
        candidates = [n for n in candidates if n.slug not in history]
        candidates, filt2 = repeat_filter.filter(candidates)
        filtered.extend(filt2)
        from .router import TransitionTrace

        for n in candidates:
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
        user: User | None,
        history: deque[str],
        repeat_filter: RepeatFilter,
        preview: PreviewContext | None = None,
    ) -> tuple[Node | None, TransitionTrace]:
        try:
            candidates = await self.provider.get_transitions(
                db, node, user, node.workspace_id, preview=preview
            )
        except TypeError:
            candidates = await self.provider.get_transitions(
                db, node, user, node.workspace_id
            )
        candidate_slugs = [n.slug for n in candidates]
        filtered = [n.slug for n in candidates if n.slug in history]
        candidates = [n for n in candidates if n.slug not in history]
        candidates, filt2 = repeat_filter.filter(candidates)
        filtered.extend(filt2)
        from .router import TransitionTrace

        if not candidates:
            return None, TransitionTrace(candidate_slugs, filtered, {}, None)
        chosen = self._rnd.choice(candidates)
        return chosen, TransitionTrace(candidate_slugs, filtered, {}, chosen.slug)
