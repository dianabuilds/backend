from __future__ import annotations

import threading
from collections import defaultdict


class TransitionMetrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.latency_sum: dict[tuple[str, str], float] = defaultdict(float)
        self.latency_count: dict[tuple[str, str], int] = defaultdict(int)
        self.no_route: dict[tuple[str, str], int] = defaultdict(int)
        self.fallback: dict[tuple[str, str], int] = defaultdict(int)
        self.entropy_sum: dict[tuple[str, str], float] = defaultdict(float)
        self.entropy_count: dict[tuple[str, str], int] = defaultdict(int)
        self.repeat_sum: dict[tuple[str, str], float] = defaultdict(float)
        self.repeat_count: dict[tuple[str, str], int] = defaultdict(int)
        self.novelty_sum: dict[tuple[str, str], float] = defaultdict(float)
        self.novelty_count: dict[tuple[str, str], int] = defaultdict(int)

    def _key(self, tenant: str | None, mode: str | None) -> tuple[str, str]:
        return (tenant or "unknown", mode or "default")

    def observe_latency(self, tenant_id: str | None, mode: str | None, ms: float) -> None:
        key = self._key(tenant_id, mode)
        with self._lock:
            self.latency_sum[key] += float(ms)
            self.latency_count[key] += 1

    def observe_repeat_rate(self, tenant_id: str | None, mode: str | None, rate: float) -> None:
        key = self._key(tenant_id, mode)
        with self._lock:
            self.repeat_sum[key] += float(rate)
            self.repeat_count[key] += 1

    def observe_novelty_rate(self, tenant_id: str | None, mode: str | None, rate: float) -> None:
        key = self._key(tenant_id, mode)
        with self._lock:
            self.novelty_sum[key] += float(rate)
            self.novelty_count[key] += 1

    def observe_entropy(self, tenant_id: str | None, mode: str | None, entropy: float) -> None:
        key = self._key(tenant_id, mode)
        with self._lock:
            self.entropy_sum[key] += float(entropy)
            self.entropy_count[key] += 1

    def inc_no_route(self, tenant_id: str | None, mode: str | None) -> None:
        key = self._key(tenant_id, mode)
        with self._lock:
            self.no_route[key] += 1

    def inc_fallback(self, tenant_id: str | None, mode: str | None) -> None:
        key = self._key(tenant_id, mode)
        with self._lock:
            self.fallback[key] += 1

    def prometheus(self) -> str:
        lines = []
        lines.append("# HELP transition_latency_ms Average transition latency (ms)")
        lines.append("# TYPE transition_latency_ms gauge")
        with self._lock:
            keys = set(self.latency_count.keys())
            for key in keys:
                ws, mode = key
                count = self.latency_count[key]
                avg = self.latency_sum[key] / count if count else 0.0
                lines.append(f'transition_latency_ms{{tenant_id="{ws}",mode="{mode}"}} {avg}')
                no_r = self.no_route.get(key, 0)
                fb = self.fallback.get(key, 0)
                nr_ratio = no_r / count if count else 0.0
                fb_ratio = fb / count if count else 0.0
                lines.append(f'no_route_ratio{{tenant_id="{ws}",mode="{mode}"}} {nr_ratio}')
                lines.append(f'fallback_ratio{{tenant_id="{ws}",mode="{mode}"}} {fb_ratio}')
                ent_sum = self.entropy_sum.get(key, 0.0)
                ent_cnt = self.entropy_count.get(key, 0)
                ent_avg = ent_sum / ent_cnt if ent_cnt else 0.0
                lines.append(f'entropy{{tenant_id="{ws}",mode="{mode}"}} {ent_avg}')
                rep_sum = self.repeat_sum.get(key, 0.0)
                rep_cnt = self.repeat_count.get(key, 0)
                rep_avg = rep_sum / rep_cnt if rep_cnt else 0.0
                lines.append(f'repeat_rate{{tenant_id="{ws}",mode="{mode}"}} {rep_avg}')
                nov_sum = self.novelty_sum.get(key, 0.0)
                nov_cnt = self.novelty_count.get(key, 0)
                nov_avg = nov_sum / nov_cnt if nov_cnt else 0.0
                lines.append(f'novelty_rate{{tenant_id="{ws}",mode="{mode}"}} {nov_avg}')
        return "\n".join(lines) + "\n"

    def snapshot(self) -> list[dict[str, object]]:
        """JSON snapshot with averages/ratios per (tenant, mode)."""
        out: list[dict[str, object]] = []
        with self._lock:
            keys = set(self.latency_count.keys())
            for key in keys:
                ws, mode = key
                count = self.latency_count.get(key, 0)
                avg = (self.latency_sum.get(key, 0.0) / count) if count else 0.0
                no_r = self.no_route.get(key, 0)
                fb = self.fallback.get(key, 0)
                nr_ratio = (no_r / count) if count else 0.0
                fb_ratio = (fb / count) if count else 0.0
                ent_avg = self.entropy_sum.get(key, 0.0) / max(self.entropy_count.get(key, 0), 1)
                rep_avg = self.repeat_sum.get(key, 0.0) / max(self.repeat_count.get(key, 0), 1)
                nov_avg = self.novelty_sum.get(key, 0.0) / max(self.novelty_count.get(key, 0), 1)
                out.append(
                    {
                        "tenant_id": ws,
                        "mode": mode,
                        "avg_latency_ms": avg,
                        "no_route_ratio": nr_ratio,
                        "fallback_ratio": fb_ratio,
                        "entropy": ent_avg,
                        "repeat_rate": rep_avg,
                        "novelty_rate": nov_avg,
                        "count": count,
                    }
                )
        return out


transition_metrics = TransitionMetrics()

__all__ = ["transition_metrics", "TransitionMetrics"]
