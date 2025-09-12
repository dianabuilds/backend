from __future__ import annotations

# Moved from app.core.metrics; see that module for shim

import json
import math
import threading
import time
from collections import defaultdict, deque
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass
class RequestRecord:
    ts: float
    duration_ms: int
    status_code: int
    method: str
    route: str
    tenant_id: str | None


def _status_class(code: int) -> str:
    if code < 200:
        return "1xx"
    if code < 300:
        return "2xx"
    if code < 400:
        return "3xx"
    if code < 500:
        return "4xx"
    return "5xx"


def _percentile(values: list[int], p: float) -> float:
    if not values:
        return 0.0
    values_sorted = sorted(values)
    k = max(int(math.ceil(p * len(values_sorted))) - 1, 0)
    return float(values_sorted[k])


class MetricsStorage:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records: deque[RequestRecord] = deque()

    def record(self, duration_ms: int, status_code: int, method: str, route: str, tenant_id: str | None = None) -> None:
        now = time.time()
        with self._lock:
            self._records.append(RequestRecord(now, duration_ms, status_code, method, route, tenant_id))
            cutoff = now - 24 * 3600
            while self._records and self._records[0].ts < cutoff:
                self._records.popleft()

    def reset(self) -> None:
        with self._lock:
            self._records.clear()

    def _select_recent(self, range_seconds: int, tenant_id: str | None = None) -> list[RequestRecord]:
        now = time.time()
        cutoff = now - range_seconds
        with self._lock:
            return [r for r in self._records if r.ts >= cutoff and (tenant_id is None or r.tenant_id == tenant_id)]

    def summary(self, range_seconds: int, tenant_id: str | None = None) -> dict:
        recent = self._select_recent(range_seconds, tenant_id)
        total = len(recent)
        if total == 0:
            return {"count": 0, "error_count": 0, "rps": 0.0, "error_rate": 0.0, "p95_latency": 0.0, "p99_latency": 0.0, "count_429": 0}
        errors = sum(1 for r in recent if r.status_code >= 400)
        durations = [r.duration_ms for r in recent]
        p95 = _percentile(durations, 0.95)
        p99 = _percentile(durations, 0.99)
        count_429 = sum(1 for r in recent if r.status_code == 429)
        return {"count": total, "error_count": errors, "rps": total / range_seconds, "error_rate": errors / total, "p95_latency": p95, "p99_latency": p99, "count_429": count_429}

    def reliability(self, range_seconds: int, tenant_id: str | None = None) -> dict:
        recent = self._select_recent(range_seconds, tenant_id)
        durations = [r.duration_ms for r in recent]
        total = len(durations)
        p95 = _percentile(durations, 0.95) if durations else 0.0
        count_4xx = sum(1 for r in recent if 400 <= r.status_code < 500)
        count_5xx = sum(1 for r in recent if r.status_code >= 500)
        return {"total": total, "p95": p95, "count_4xx": count_4xx, "count_5xx": count_5xx}

    def timeseries(self, range_seconds: int, step_seconds: int, tenant_id: str | None = None) -> dict:
        recent = self._select_recent(range_seconds, tenant_id)
        now = time.time()
        buckets: dict[int, list[RequestRecord]] = defaultdict(list)
        for r in recent:
            idx = int((now - r.ts) // step_seconds)
            buckets[idx].append(r)
        max_idx = int(range_seconds // step_seconds)
        out = {
            "labels": [int(now - i * step_seconds) for i in range(max_idx, -1, -1)],
            "values": {"count": [], "p95": [], "2xx": [], "3xx": [], "4xx": [], "5xx": []},
        }
        for i in range(max_idx, -1, -1):
            recs = buckets.get(i, [])
            out["values"]["count"].append(len(recs))
            if recs:
                durations = [r.duration_ms for r in recs]
                out["values"]["p95"].append(_percentile(durations, 0.95))
                classes = defaultdict(int)
                for r in recs:
                    classes[_status_class(r.status_code)] += 1
                for c in ["2xx", "3xx", "4xx", "5xx"]:
                    out["values"][c].append(classes.get(c, 0))
            else:
                out["values"]["p95"].append(0.0)
                for c in ["2xx", "3xx", "4xx", "5xx"]:
                    out["values"][c].append(0)
        return out

    def prometheus(self, range_seconds: int = 300, tenant_id: str | None = None) -> str:
        recent = self._select_recent(range_seconds, tenant_id)
        durations = [r.duration_ms for r in recent]
        lines: list[str] = []
        lines.append("# HELP http_request_duration_ms Request duration in milliseconds")
        lines.append("# TYPE http_request_duration_ms summary")
        if durations:
            avg = sum(durations) / len(durations)
            p95 = _percentile(durations, 0.95)
            lines.append(f"http_request_duration_ms_avg {avg}")
            lines.append(f"http_request_duration_ms_p95 {p95}")
        else:
            lines.append("http_request_duration_ms_avg 0")
            lines.append("http_request_duration_ms_p95 0")
        counts = defaultdict(int)
        for r in recent:
            counts[_status_class(r.status_code)] += 1
        lines.append("# HELP http_requests_total Total HTTP requests by status class")
        lines.append("# TYPE http_requests_total counter")
        for cls in ["2xx", "3xx", "4xx", "5xx"]:
            lines.append(f'http_requests_total{{class="{cls}"}} {counts.get(cls, 0)}')
        return "\n".join(lines) + "\n"


metrics_storage = MetricsStorage()

__all__ = ["metrics_storage", "MetricsStorage", "RequestRecord"]

