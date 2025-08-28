from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable, List, Set
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.preview import PreviewContext
from app.domains.quests.infrastructure.models.navigation_cache_models import (
    NavigationCache,
)
from app.domains.quests.infrastructure.models.quest_version_models import (
    QuestGraphEdge,
    QuestGraphNode,
    QuestVersion,
)
from app.domains.quests.schemas import QuestStep, QuestTransition
from app.schemas.quest_editor import SimulateIn, SimulateResult, ValidateResult


class EditorService:
    def __init__(self) -> None:
        pass

    async def create_version(
        self,
        db: AsyncSession,
        quest_id: UUID,
        actor_id: UUID | None = None,
    ) -> QuestVersion:
        """Create a new draft version for the quest."""

        max_num = (
            await db.execute(
                select(func.max(QuestVersion.number)).where(
                    QuestVersion.quest_id == quest_id
                )
            )
        ).scalar() or 0

        version = QuestVersion(
            quest_id=quest_id,
            number=int(max_num) + 1,
            status="draft",
            created_at=datetime.utcnow(),
            created_by=actor_id,
        )
        db.add(version)
        await db.flush()
        await self.invalidate_navigation_cache(db)
        return version

    async def get_version_graph(
        self, db: AsyncSession, version_id: UUID
    ) -> tuple[QuestVersion, List[QuestStep], List[QuestTransition]]:
        version = await db.get(QuestVersion, version_id)
        if not version:
            raise ValueError("version_not_found")

        nodes: Iterable[QuestGraphNode] = (
            await db.execute(
                select(QuestGraphNode).where(QuestGraphNode.version_id == version_id)
            )
        ).scalars().all()
        edges: Iterable[QuestGraphEdge] = (
            await db.execute(
                select(QuestGraphEdge).where(QuestGraphEdge.version_id == version_id)
            )
        ).scalars().all()

        steps = [
            QuestStep(
                key=n.key,
                title=n.title,
                type=n.type,
                content=n.content,
                rewards=n.rewards,
            )
            for n in nodes
        ]
        transitions = [
            QuestTransition(
                from_node_key=e.from_node_key,
                to_node_key=e.to_node_key,
                label=e.label,
                condition=e.condition,
            )
            for e in edges
        ]

        return version, steps, transitions

    async def replace_graph(
        self,
        db: AsyncSession,
        version_id: UUID,
        steps: List[QuestStep],
        transitions: List[QuestTransition],
    ) -> None:
        await db.execute(
            delete(QuestGraphEdge).where(QuestGraphEdge.version_id == version_id)
        )
        await db.execute(
            delete(QuestGraphNode).where(QuestGraphNode.version_id == version_id)
        )
        await db.flush()

        for s in steps:
            db.add(
                QuestGraphNode(
                    version_id=version_id,
                    key=s.key,
                    title=s.title,
                    type=s.type,
                    content=s.content,
                    rewards=s.rewards,
                )
            )
        for t in transitions:
            db.add(
                QuestGraphEdge(
                    version_id=version_id,
                    from_node_key=t.from_node_key,
                    to_node_key=t.to_node_key,
                    label=t.label,
                    condition=t.condition,
                )
            )

        await db.flush()
        await self.invalidate_navigation_cache(db)
        await self.generate_navigation_cache(db, version_id)

    async def delete_version(self, db: AsyncSession, version_id: UUID) -> None:
        version = await db.get(QuestVersion, version_id)
        if not version:
            raise ValueError("version_not_found")
        await db.delete(version)
        await db.flush()
        await self.invalidate_navigation_cache(db)

    async def validate_version(
        self, db: AsyncSession, version_id: UUID
    ) -> ValidateResult:
        _, steps, transitions = await self.get_version_graph(db, version_id)
        return self.validate_graph(steps, transitions)

    async def simulate_version(
        self,
        db: AsyncSession,
        version_id: UUID,
        payload: SimulateIn,
        preview: PreviewContext | None = None,
    ) -> SimulateResult:
        _, steps, transitions = await self.get_version_graph(db, version_id)
        return self.simulate_graph(steps, transitions, payload, preview)

    def validate_graph(
        self, nodes: List[QuestStep], edges: List[QuestTransition]
    ) -> ValidateResult:
        errors: List[str] = []
        warnings: List[str] = []

        node_keys: Set[str] = set()
        node_map: Dict[str, QuestStep] = {}
        start_count = 0
        end_count = 0
        for n in nodes:
            if n.key in node_keys:
                errors.append(f"Duplicate node key: {n.key}")
            node_keys.add(n.key)
            node_map[n.key] = n
            if n.type == "start":
                start_count += 1
            if n.type == "end":
                end_count += 1

        if start_count != 1:
            errors.append("There must be exactly one start node")
        if end_count < 1:
            errors.append("There must be at least one end node")

        adj: Dict[str, List[str]] = {}
        adj_edges: Dict[str, List[QuestTransition]] = {}
        incoming: Dict[str, int] = {k: 0 for k in node_keys}
        for e in edges:
            if e.from_node_key not in node_keys:
                errors.append(f"Edge from unknown node: {e.from_node_key}")
                continue
            if e.to_node_key not in node_keys:
                errors.append(f"Edge to unknown node: {e.to_node_key}")
                continue
            adj.setdefault(e.from_node_key, []).append(e.to_node_key)
            adj_edges.setdefault(e.from_node_key, []).append(e)
            incoming[e.to_node_key] = incoming.get(e.to_node_key, 0) + 1

        start_key = next((n.key for n in nodes if n.type == "start"), None)
        if start_key and not errors:
            seen: Set[str] = set()
            stack = [start_key]
            while stack:
                cur = stack.pop()
                if cur in seen:
                    continue
                seen.add(cur)
                for nx in adj.get(cur, []):
                    if nx not in seen:
                        stack.append(nx)
            for k in node_keys:
                if k not in seen:
                    if node_map[k].type == "end":
                        errors.append(f"End node not reachable: {k}")
                    else:
                        errors.append(f"Unreachable node: {k}")

        for k in node_keys:
            if incoming.get(k, 0) == 0 and len(adj.get(k, [])) == 0:
                errors.append(f"Isolated node: {k}")

        for n in nodes:
            outs = adj_edges.get(n.key, [])
            if n.type != "end" and len(outs) == 0:
                warnings.append(f"Node has no outgoing edges: {n.key}")
            if len([e for e in outs if e.condition is None]) > 1:
                errors.append(f"Multiple unconditional transitions from node: {n.key}")

        # Detect unconditional cycles (including self-loops)
        index = 0
        stack: List[str] = []
        indices: Dict[str, int] = {}
        lowlink: Dict[str, int] = {}
        onstack: Set[str] = set()
        sccs: List[List[str]] = []

        def strongconnect(v: str) -> None:
            nonlocal index
            indices[v] = index
            lowlink[v] = index
            index += 1
            stack.append(v)
            onstack.add(v)
            for e in adj_edges.get(v, []):
                w = e.to_node_key
                if w not in indices:
                    strongconnect(w)
                    lowlink[v] = min(lowlink[v], lowlink[w])
                elif w in onstack:
                    lowlink[v] = min(lowlink[v], indices[w])
            if lowlink[v] == indices[v]:
                comp: List[str] = []
                while True:
                    w = stack.pop()
                    onstack.remove(w)
                    comp.append(w)
                    if w == v:
                        break
                sccs.append(comp)

        for v in node_keys:
            if v not in indices:
                strongconnect(v)

        for comp in sccs:
            edges_in_comp = [
                e
                for e in edges
                if e.from_node_key in comp and e.to_node_key in comp
            ]
            if len(comp) == 1:
                if any(
                    e.from_node_key == comp[0]
                    and e.to_node_key == comp[0]
                    and e.condition is None
                    for e in edges_in_comp
                ):
                    errors.append(f"Unconditional loop at node: {comp[0]}")
            elif edges_in_comp and all(e.condition is None for e in edges_in_comp):
                errors.append(
                    "Unconditional loop between nodes: "
                    + ", ".join(sorted(comp))
                )

        ok = len([e for e in errors if e]) == 0
        return ValidateResult(ok=ok, errors=errors, warnings=warnings)

    def simulate_graph(
        self,
        nodes: List[QuestStep],
        edges: List[QuestTransition],
        payload: SimulateIn,
        preview: PreviewContext | None = None,
    ) -> SimulateResult:
        key_to_node = {n.key: n for n in nodes}
        adj: Dict[str, List[QuestTransition]] = {}
        for e in edges:
            adj.setdefault(e.from_node_key, []).append(e)

        steps: List[dict] = []
        rewards: List[dict] = []

        start = next((n for n in nodes if n.type == "start"), None)
        if not start:
            return SimulateResult(steps=[], rewards=[])

        cur = start
        visited = set()
        while cur and cur.key not in visited:
            visited.add(cur.key)
            steps.append({"node": cur.key, "title": cur.title})
            if cur.rewards:
                rewards.append({"node": cur.key, **cur.rewards})
            outs = adj.get(cur.key, [])
            if not outs:
                break
            nxt = outs[0]
            steps.append(
                {"edge": f"{nxt.from_node_key}->{nxt.to_node_key}", "label": nxt.label}
            )
            cur = key_to_node.get(nxt.to_node_key)
            if not cur:
                break

        return SimulateResult(steps=steps, rewards=rewards)

    async def invalidate_navigation_cache(self, db: AsyncSession) -> None:
        await db.execute(delete(NavigationCache))
        await db.flush()

    async def generate_navigation_cache(
        self, db: AsyncSession, version_id: UUID
    ) -> None:
        version, steps, transitions = await self.get_version_graph(db, version_id)
        await db.execute(delete(NavigationCache))
        adj: Dict[str, List[str]] = {}
        for t in transitions:
            adj.setdefault(t.from_node_key, []).append(t.to_node_key)
        now = datetime.utcnow().isoformat()
        for s in steps:
            data = {
                "mode": "auto",
                "transitions": [
                    {"slug": dst, "title": dst, "source_type": "cached"}
                    for dst in adj.get(s.key, [])
                ],
                "generated_at": now,
            }
            db.add(
                NavigationCache(
                    node_slug=s.key,
                    navigation=data,
                    compass=[],
                    echo=[],
                )
            )
        await db.flush()
