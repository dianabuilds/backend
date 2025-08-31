from __future__ import annotations

from collections import defaultdict
from uuid import UUID

# mypy: ignore-errors
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.navigation.infrastructure.models.transition_models import (
    NodeTransition,
)
from app.domains.navigation.schemas.problems import NavigationNodeProblem
from app.domains.nodes.infrastructure.models.node import Node


class NavigationProblemsService:
    """Analyse navigation graph for CTR, cycles and dead-ends."""

    async def analyse(self, db: AsyncSession) -> list[NavigationNodeProblem]:
        node_rows = (
            await db.execute(select(Node.id, Node.slug, Node.title, Node.views))
        ).all()
        nodes: dict[UUID, dict] = {
            row.id: {
                "slug": row.slug,
                "title": row.title,
                "views": row.views or 0,
            }
            for row in node_rows
        }

        transition_rows = (
            await db.execute(
                select(NodeTransition.from_node_id, NodeTransition.to_node_id)
            )
        ).all()

        adjacency: dict[UUID, list[UUID]] = defaultdict(list)
        for frm, to in transition_rows:
            adjacency[frm].append(to)

        # detect cycles using Tarjan's algorithm
        index = 0
        indices: dict[UUID, int] = {}
        lowlink: dict[UUID, int] = {}
        stack: list[UUID] = []
        on_stack: set[UUID] = set()
        cycles: set[UUID] = set()

        def strongconnect(v: UUID) -> None:
            nonlocal index
            indices[v] = index
            lowlink[v] = index
            index += 1
            stack.append(v)
            on_stack.add(v)
            for w in adjacency.get(v, []):
                if w not in indices:
                    strongconnect(w)
                    lowlink[v] = min(lowlink[v], lowlink[w])
                elif w in on_stack:
                    lowlink[v] = min(lowlink[v], indices[w])
            if lowlink[v] == indices[v]:
                component: list[UUID] = []
                while True:
                    w = stack.pop()
                    on_stack.remove(w)
                    component.append(w)
                    if w == v:
                        break
                if len(component) > 1:
                    cycles.update(component)
                else:
                    node = component[0]
                    if node in adjacency.get(node, []):
                        cycles.add(node)

        for v in nodes.keys():
            if v not in indices:
                strongconnect(v)

        problems: list[NavigationNodeProblem] = []
        for node_id, data in nodes.items():
            outgoing = len(adjacency.get(node_id, []))
            views = data["views"]
            ctr = (outgoing / views) if views else 0.0
            problems.append(
                NavigationNodeProblem(
                    node_id=node_id,
                    slug=data["slug"],
                    title=data["title"],
                    views=views,
                    transitions=outgoing,
                    ctr=ctr,
                    dead_end=outgoing == 0,
                    cycle=node_id in cycles,
                )
            )
        return problems
