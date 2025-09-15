from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence


class TagUsageStore:
    """Per-user tag usage counters with optional content_type dimension."""

    def __init__(self) -> None:
        # author_id -> content_type -> slug -> count
        self._cnt: dict[str, dict[str, dict[str, int]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(int))
        )

    def apply_diff(
        self,
        author_id: str,
        added: Sequence[str],
        removed: Sequence[str],
        *,
        content_type: str = "node",
    ) -> None:
        aid = str(author_id)
        ctype = str(content_type or "node")
        for s in added:
            self._cnt[aid][ctype][str(s)] += 1
        for s in removed:
            x = self._cnt[aid][ctype].get(str(s), 0) - 1
            if x <= 0:
                self._cnt[aid][ctype].pop(str(s), None)
            else:
                self._cnt[aid][ctype][str(s)] = x

    def list_for_user(
        self,
        user_id: str,
        q: str | None,
        popular: bool,
        limit: int,
        offset: int,
        content_type: str | None,
    ) -> list[tuple[str, int]]:
        # merge counts across content types if content_type is None

        def _filter(items: dict[str, int]):
            if q:
                return {k: v for k, v in items.items() if q.lower() in k.lower()}
            return items

        aid = str(user_id)
        if content_type:
            data = _filter(self._cnt[aid].get(content_type, {}))
        else:
            merged: dict[str, int] = defaultdict(int)
            for _ctype, sub in self._cnt[aid].items():
                for k, v in sub.items():
                    merged[k] += v
            data = _filter(merged)
        pairs = list(data.items())
        pairs.sort(key=(lambda kv: (-kv[1], kv[0])) if popular else (lambda kv: kv[0]))
        return pairs[offset : offset + limit]
