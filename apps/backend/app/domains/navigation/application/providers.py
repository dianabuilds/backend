from __future__ import annotations

import random
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.preview import PreviewContext  # isort: skip

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from app.domains.navigation.application.compass_service import CompassService
    from app.domains.navigation.application.echo_service import EchoService
    from app.domains.navigation.application.transitions_service import (
        TransitionsService,
    )
    from app.domains.nodes.infrastructure.models.node import Node
    from app.domains.users.infrastructure.models.user import User


class TransitionProvider(ABC):
    """Interface for objects that return possible transitions from a node."""

    @abstractmethod
    async def get_transitions(
        self,
        db: AsyncSession,
        node: Node,
        user: User | None,
        space_id: int,
        preview: PreviewContext | None = None,
    ) -> Sequence[Node]:
        """Return candidate nodes for transition."""


class ManualTransitionsProvider(TransitionProvider):
    def __init__(self, service: TransitionsService | None = None) -> None:
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
        user: User | None,
        space_id: int,
        preview: PreviewContext | None = None,
    ) -> Sequence[Node]:
        transitions = await self._service.get_transitions(db, node, user, space_id, preview=preview)
        nodes: list[Node] = []
        for t in transitions:
            n = t.to_node
            n.weight = t.weight
            nodes.append(n)
        return nodes


class CompassProvider(TransitionProvider):
    def __init__(self, service: CompassService | None = None, limit: int = 5) -> None:
        if service is None:
            from app.domains.navigation.application.compass_service import (
                CompassService,
            )

            service = CompassService()
        self._service = service
        self._limit = limit

    async def get_transitions(
        self,
        db: AsyncSession,
        node: Node,
        user: User | None,
        space_id: int,
        preview: PreviewContext | None = None,
    ) -> Sequence[Node]:
        return await self._service.get_compass_nodes(
            db, node, user, self._limit, preview=preview, space_id=space_id
        )


class EchoProvider(TransitionProvider):
    def __init__(self, service: EchoService | None = None, limit: int = 3) -> None:
        if service is None:
            from app.domains.navigation.application.echo_service import EchoService

            service = EchoService()
        self._service = service
        self._limit = limit

    async def get_transitions(
        self,
        db: AsyncSession,
        node: Node,
        user: User | None,
        space_id: int,
        preview: PreviewContext | None = None,
    ) -> Sequence[Node]:
        return await self._service.get_echo_transitions(
            db, node, self._limit, user=user, preview=preview, space_id=space_id
        )


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
        user: User | None,
        space_id: int,
        preview: PreviewContext | None = None,
    ) -> Sequence[Node]:
        from app.domains.accounts.application.service import scope_by_account
        from app.domains.navigation.application.access_policy import has_access_async
        from app.domains.nodes.infrastructure.models.node import Node

        query = select(Node).where(
            Node.is_visible,
            Node.is_public,
            Node.is_recommendable,
            Node.id != node.id,
        )
        if hasattr(Node, "workspace_id"):
            query = query.where(Node.workspace_id == space_id)
        else:
            query = query.where(Node.account_id == space_id)
        query = scope_by_account(query, space_id)
        result = await db.execute(query)
        nodes: list[Node] = result.scalars().all()
        nodes = [n for n in nodes if await has_access_async(n, user, preview)]
        if not nodes:
            return []
        return [self._rnd.choice(nodes)]
