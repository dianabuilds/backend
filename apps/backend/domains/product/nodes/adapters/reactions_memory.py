from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from itertools import count

from domains.product.nodes.application.ports import (
    NodeReactionDTO,
    NodeReactionsRepo,
)


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class MemoryNodeReactionsRepo(NodeReactionsRepo):
    def __init__(self) -> None:
        self._id_seq = count(1)
        self._entries: dict[int, NodeReactionDTO] = {}
        self._by_node: dict[int, dict[str, dict[str, int]]] = defaultdict(
            lambda: defaultdict(dict)
        )

    async def add(
        self, node_id: int, user_id: str, reaction_type: str = "like"
    ) -> bool:
        reaction = (reaction_type or "like").strip().lower() or "like"
        node_key = int(node_id)
        user_map = self._by_node[node_key][reaction]
        if user_id in user_map:
            return False
        reaction_id = next(self._id_seq)
        dto = NodeReactionDTO(
            id=reaction_id,
            node_id=node_key,
            user_id=str(user_id),
            reaction_type=reaction,
            created_at=_now_iso(),
        )
        user_map[user_id] = reaction_id
        self._entries[reaction_id] = dto
        return True

    async def remove(
        self, node_id: int, user_id: str, reaction_type: str = "like"
    ) -> bool:
        reaction = (reaction_type or "like").strip().lower() or "like"
        node_key = int(node_id)
        user_map = self._by_node.get(node_key, {}).get(reaction)
        if not user_map:
            return False
        reaction_id = user_map.pop(user_id, None)
        if reaction_id is None:
            return False
        self._entries.pop(reaction_id, None)
        if not user_map:
            self._by_node[node_key].pop(reaction, None)
        if not self._by_node[node_key]:
            self._by_node.pop(node_key, None)
        return True

    async def has(
        self, node_id: int, user_id: str, reaction_type: str = "like"
    ) -> bool:
        reaction = (reaction_type or "like").strip().lower() or "like"
        node_key = int(node_id)
        return user_id in self._by_node.get(node_key, {}).get(reaction, {})

    async def counts(self, node_id: int) -> dict[str, int]:
        node_map = self._by_node.get(int(node_id), {})
        return {reaction: len(users) for reaction, users in node_map.items()}

    async def list_for_node(
        self, node_id: int, *, limit: int = 100, offset: int = 0
    ) -> list[NodeReactionDTO]:
        node_map = self._by_node.get(int(node_id), {})
        if not node_map:
            return []
        reaction_ids: list[int] = []
        for users in node_map.values():
            reaction_ids.extend(users.values())
        dtos = [self._entries[rid] for rid in reaction_ids]
        dtos.sort(key=lambda dto: dto.id, reverse=True)
        return dtos[offset : offset + limit]


__all__ = ["MemoryNodeReactionsRepo"]
