from __future__ import annotations

from datetime import UTC, datetime

from domains.product.nodes.application.ports import NodeViewsRepo, NodeViewStat


def _parse_at(value: str | None) -> datetime:
    if not value:
        return datetime.now(UTC)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    except ValueError:
        return datetime.now(UTC)


class MemoryNodeViewsRepo(NodeViewsRepo):
    def __init__(self) -> None:
        self._totals: dict[int, int] = {}
        self._daily: dict[int, dict[str, int]] = {}

    async def increment(
        self,
        node_id: int,
        *,
        amount: int = 1,
        viewer_id: str | None = None,
        fingerprint: str | None = None,
        at: str | None = None,
    ) -> int:
        delta = int(amount)
        if delta <= 0:
            raise ValueError("amount_positive_required")
        when = _parse_at(at)
        bucket_key = when.date().isoformat()
        node_key = int(node_id)
        total = self._totals.get(node_key, 0) + delta
        self._totals[node_key] = total
        per_node = self._daily.setdefault(node_key, {})
        per_node[bucket_key] = per_node.get(bucket_key, 0) + delta
        return total

    async def get_total(self, node_id: int) -> int:
        return self._totals.get(int(node_id), 0)

    async def get_daily(
        self, node_id: int, *, limit: int = 30, offset: int = 0
    ) -> list[NodeViewStat]:
        per_node = self._daily.get(int(node_id), {})
        if not per_node:
            return []
        ordered = sorted(per_node.items(), key=lambda item: item[0], reverse=True)
        sliced = ordered[offset : offset + limit]
        return [
            NodeViewStat(node_id=int(node_id), bucket_date=bucket, views=int(views))
            for bucket, views in sliced
        ]


__all__ = ["MemoryNodeViewsRepo"]
