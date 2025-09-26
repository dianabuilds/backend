from __future__ import annotations

from dataclasses import dataclass


@dataclass
class _QueryStat:
    count: int = 0
    results: int = 0


class SearchStatsService:
    """In-memory aggregation of search queries."""

    def __init__(self) -> None:
        self._stats: dict[str, _QueryStat] = {}

    def record(self, query: str, results: int) -> None:
        if not query:
            return
        stat = self._stats.setdefault(query, _QueryStat())
        stat.count += 1
        stat.results = results

    def top(self, limit: int = 10) -> list[dict[str, int | str]]:
        items = sorted(self._stats.items(), key=lambda kv: kv[1].count, reverse=True)
        return [{"query": q, "count": s.count, "results": s.results} for q, s in items[:limit]]

    def reset(self) -> None:
        self._stats.clear()


search_stats = SearchStatsService()

__all__ = ["search_stats", "SearchStatsService"]
