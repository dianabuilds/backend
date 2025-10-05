from __future__ import annotations

from collections import defaultdict, deque
from datetime import UTC, datetime
from itertools import count
from typing import Any

from domains.product.nodes.application.ports import (
    NodeCommentBanDTO,
    NodeCommentDTO,
    NodeCommentsRepo,
)

_MAX_DEPTH = 5


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_status(value: str) -> str:
    normalized = (value or "").strip().lower()
    if not normalized:
        raise ValueError("status_required")
    return normalized


def _clone_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in metadata.items()}


def _dto_from_state(state: dict[str, Any]) -> NodeCommentDTO:
    return NodeCommentDTO(
        id=int(state["id"]),
        node_id=int(state["node_id"]),
        author_id=str(state["author_id"]),
        parent_comment_id=(
            int(state["parent_comment_id"])
            if state["parent_comment_id"] is not None
            else None
        ),
        depth=int(state["depth"]),
        content=str(state["content"]),
        status=str(state["status"]),
        metadata=_clone_metadata(state["metadata"]),
        created_at=str(state["created_at"]),
        updated_at=str(state["updated_at"]),
    )


class MemoryNodeCommentsRepo(NodeCommentsRepo):
    def __init__(self) -> None:
        self._id_seq = count(1)
        self._comments: dict[int, dict[str, Any]] = {}
        self._by_node: dict[int, dict[int | None, list[int]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._bans: dict[tuple[int, str], NodeCommentBanDTO] = {}
        self._locks: dict[int, dict[str, str | None]] = {}
        self._disabled: set[int] = set()

    async def create(
        self,
        *,
        node_id: int,
        author_id: str,
        content: str,
        parent_comment_id: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> NodeCommentDTO:
        node_key = int(node_id)
        parent_id = parent_comment_id
        depth = 0
        if parent_id is not None:
            parent_state = self._comments.get(int(parent_id))
            if parent_state is None:
                raise ValueError("parent_not_found")
            if int(parent_state["node_id"]) != node_key:
                raise ValueError("parent_node_mismatch")
            depth = int(parent_state["depth"]) + 1
            if depth > _MAX_DEPTH:
                raise ValueError("comment_depth_exceeded")
        comment_id = next(self._id_seq)
        created = _now_iso()
        state = {
            "id": comment_id,
            "node_id": node_key,
            "author_id": str(author_id),
            "parent_comment_id": parent_id,
            "depth": depth,
            "content": str(content),
            "status": "published",
            "metadata": dict(metadata or {}),
            "created_at": created,
            "updated_at": created,
        }
        self._comments[comment_id] = state
        self._by_node[node_key][parent_id].append(comment_id)
        return _dto_from_state(state)

    async def get(self, comment_id: int) -> NodeCommentDTO | None:
        state = self._comments.get(int(comment_id))
        return _dto_from_state(state) if state else None

    async def list_for_node(
        self,
        node_id: int,
        *,
        parent_comment_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> list[NodeCommentDTO]:
        node_map = self._by_node.get(int(node_id), {})
        ids = node_map.get(parent_comment_id, [])
        if not ids:
            return []
        dtos: list[NodeCommentDTO] = []
        for cid in ids:
            state = self._comments.get(cid)
            if state is None:
                continue
            if not include_deleted and state["status"] in {
                "deleted",
                "hidden",
                "blocked",
            }:
                continue
            dtos.append(_dto_from_state(state))
        dtos.sort(key=lambda dto: dto.created_at)
        return dtos[offset : offset + limit]

    async def update_status(
        self,
        comment_id: int,
        status: str,
        *,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> NodeCommentDTO:
        state = self._comments.get(int(comment_id))
        if state is None:
            raise ValueError("comment_not_found")
        normalized = _normalize_status(status)
        history = state["metadata"].setdefault("history", [])
        history.append(
            {
                "status": normalized,
                "actor_id": actor_id,
                "reason": reason,
                "at": _now_iso(),
            }
        )
        state["status"] = normalized
        state["updated_at"] = _now_iso()
        return _dto_from_state(state)

    async def soft_delete(
        self,
        comment_id: int,
        *,
        actor_id: str,
        reason: str | None = None,
    ) -> bool:
        state = self._comments.get(int(comment_id))
        if state is None:
            return False
        history = state["metadata"].setdefault("history", [])
        history.append(
            {
                "status": "deleted",
                "actor_id": actor_id,
                "reason": reason,
                "at": _now_iso(),
            }
        )
        state["status"] = "deleted"
        state["updated_at"] = _now_iso()
        return True

    async def hard_delete(self, comment_id: int) -> bool:
        comment_id = int(comment_id)
        state = self._comments.pop(comment_id, None)
        if state is None:
            return False
        node_key = int(state["node_id"])
        parent_id = state["parent_comment_id"]
        self._remove_child_reference(node_key, parent_id, comment_id)
        queue = deque(self._by_node.get(node_key, {}).get(comment_id, []))
        while queue:
            child_id = queue.popleft()
            child = self._comments.pop(child_id, None)
            if child is None:
                continue
            grand_children = self._by_node.get(node_key, {}).get(child_id, [])
            queue.extend(grand_children)
            self._remove_child_reference(node_key, child["parent_comment_id"], child_id)
        self._by_node.get(node_key, {}).pop(comment_id, None)
        return True

    def _remove_child_reference(
        self, node_key: int, parent_id: int | None, comment_id: int
    ) -> None:
        node_map = self._by_node.get(node_key)
        if not node_map:
            return
        siblings = node_map.get(parent_id)
        if not siblings:
            return
        try:
            siblings.remove(comment_id)
        except ValueError:
            return

    async def lock_node(
        self,
        node_id: int,
        *,
        locked_by: str | None,
        locked_at: str | None,
        reason: str | None = None,
    ) -> None:
        self._locks[int(node_id)] = {
            "locked_by": locked_by,
            "locked_at": locked_at,
            "reason": reason,
        }

    async def set_comments_disabled(
        self,
        node_id: int,
        *,
        disabled: bool,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> None:
        if disabled:
            self._disabled.add(int(node_id))
        else:
            self._disabled.discard(int(node_id))

    async def record_ban(
        self,
        node_id: int,
        target_user_id: str,
        *,
        set_by: str,
        reason: str | None = None,
    ) -> NodeCommentBanDTO:
        dto = NodeCommentBanDTO(
            node_id=int(node_id),
            target_user_id=str(target_user_id),
            set_by=str(set_by),
            reason=reason,
            created_at=_now_iso(),
        )
        self._bans[(int(node_id), str(target_user_id))] = dto
        return dto

    async def remove_ban(self, node_id: int, target_user_id: str) -> bool:
        key = (int(node_id), str(target_user_id))
        return self._bans.pop(key, None) is not None

    async def is_banned(self, node_id: int, target_user_id: str) -> bool:
        return (int(node_id), str(target_user_id)) in self._bans

    async def list_bans(self, node_id: int) -> list[NodeCommentBanDTO]:
        items = [dto for (nid, _), dto in self._bans.items() if nid == int(node_id)]
        items.sort(key=lambda dto: dto.created_at, reverse=True)
        return items


__all__ = ["MemoryNodeCommentsRepo"]
