from __future__ import annotations

from typing import Dict, List, Set

from app.core.preview import PreviewContext
from app.schemas.quest_editor import (
    GraphEdge,
    GraphNode,
    SimulateIn,
    SimulateResult,
    ValidateResult,
)


class EditorService:
    def validate_graph(
        self, nodes: List[GraphNode], edges: List[GraphEdge]
    ) -> ValidateResult:
        errors: List[str] = []
        warnings: List[str] = []

        node_keys: Set[str] = set()
        start_count = 0
        end_count = 0
        for n in nodes:
            if n.key in node_keys:
                errors.append(f"Duplicate node key: {n.key}")
            node_keys.add(n.key)
            if n.type == "start":
                start_count += 1
            if n.type == "end":
                end_count += 1

        if start_count != 1:
            errors.append("There must be exactly one start node")
        if end_count < 1:
            warnings.append("There is no explicit end node")

        adj: Dict[str, List[str]] = {}
        incoming: Dict[str, int] = {k: 0 for k in node_keys}
        for e in edges:
            if e.from_node_key not in node_keys:
                errors.append(f"Edge from unknown node: {e.from_node_key}")
                continue
            if e.to_node_key not in node_keys:
                errors.append(f"Edge to unknown node: {e.to_node_key}")
                continue
            adj.setdefault(e.from_node_key, []).append(e.to_node_key)
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
                    warnings.append(f"Unreachable node: {k}")

        for n in nodes:
            if n.type != "end" and len(adj.get(n.key, [])) == 0:
                warnings.append(f"Node has no outgoing edges: {n.key}")

        ok = len([e for e in errors if e]) == 0
        return ValidateResult(ok=ok, errors=errors, warnings=warnings)

    def simulate_graph(
        self,
        nodes: List[GraphNode],
        edges: List[GraphEdge],
        payload: SimulateIn,
        preview: PreviewContext | None = None,
    ) -> SimulateResult:
        key_to_node = {n.key: n for n in nodes}
        adj: Dict[str, List[GraphEdge]] = {}
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
