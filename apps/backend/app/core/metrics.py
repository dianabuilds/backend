# ruff: noqa: E501
from __future__ import annotations

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
    route: str  # шаблон маршрута, либо фактический путь, если шаблон недоступен
    scope_id: str | None


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
    """Simple in-memory storage for HTTP request metrics."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records: deque[RequestRecord] = deque()

    def record(
        self,
        duration_ms: int,
        status_code: int,
        method: str,
        route: str,
        scope_id: str | None = None,
    ) -> None:
        now = time.time()
        with self._lock:
            self._records.append(
                RequestRecord(now, duration_ms, status_code, method, route, scope_id)
            )
            # Храним не более 24 часов
            cutoff = now - 24 * 3600
            while self._records and self._records[0].ts < cutoff:
                self._records.popleft()

    def reset(self) -> None:
        with self._lock:
            self._records.clear()

    def _select_recent(
        self, range_seconds: int, scope_id: str | None = None
    ) -> list[RequestRecord]:
        now = time.time()
        cutoff = now - range_seconds
        with self._lock:
            return [
                r
                for r in self._records
                if r.ts >= cutoff and (scope_id is None or r.scope_id == scope_id)
            ]

    def summary(self, range_seconds: int, scope_id: str | None = None) -> dict:
        recent = self._select_recent(range_seconds, scope_id)
        total = len(recent)
        if total == 0:
            return {
                "count": 0,
                "error_count": 0,
                "rps": 0.0,
                "error_rate": 0.0,
                "p95_latency": 0.0,
                "p99_latency": 0.0,
                "count_429": 0,
            }
        errors = sum(1 for r in recent if r.status_code >= 400)
        durations = [r.duration_ms for r in recent]
        p95 = _percentile(durations, 0.95)
        p99 = _percentile(durations, 0.99)
        count_429 = sum(1 for r in recent if r.status_code == 429)
        return {
            "count": total,
            "error_count": errors,
            "rps": total / range_seconds,
            "error_rate": errors / total,
            "p95_latency": p95,
            "p99_latency": p99,
            "count_429": count_429,
        }

    def reliability(self, range_seconds: int, scope_id: str | None = None) -> dict:
        """Return p95 latency and error counters for the given period."""
        recent = self._select_recent(range_seconds, scope_id)
        durations = [r.duration_ms for r in recent]
        total = len(durations)
        p95 = _percentile(durations, 0.95) if durations else 0.0
        count_4xx = sum(1 for r in recent if 400 <= r.status_code < 500)
        count_5xx = sum(1 for r in recent if r.status_code >= 500)
        return {
            "total": total,
            "p95": p95,
            "count_4xx": count_4xx,
            "count_5xx": count_5xx,
        }

    def timeseries(
        self, range_seconds: int, step_seconds: int, scope_id: str | None = None
    ) -> dict:
        """Вернуть таймсерии: counts per status class и p95 latency по бакетам."""
        if step_seconds <= 0:
            step_seconds = 60
        recent = self._select_recent(range_seconds, scope_id)
        if not recent:
            return {
                "step": step_seconds,
                "from": int(time.time()) - range_seconds,
                "to": int(time.time()),
                "series": [],
                "p95": [],
            }

        buckets: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        durations: dict[int, list[int]] = defaultdict(list)

        def bucket_ts(ts: float) -> int:
            return int(ts // step_seconds * step_seconds)

        for r in recent:
            b = bucket_ts(r.ts)
            buckets[b][_status_class(r.status_code)] += 1
            durations[b].append(r.duration_ms)

        # Собираем серии по 2xx/4xx/5xx
        classes = ["2xx", "4xx", "5xx"]
        all_bucket_keys = sorted(buckets.keys())
        series = []
        for cls in classes:
            points = [{"ts": b, "value": buckets[b].get(cls, 0)} for b in all_bucket_keys]
            series.append({"name": cls, "points": points})
        # p95
        p95_points = [{"ts": b, "value": _percentile(durations[b], 0.95)} for b in all_bucket_keys]

        return {
            "step": step_seconds,
            "from": (min(all_bucket_keys) if all_bucket_keys else int(time.time()) - range_seconds),
            "to": (max(all_bucket_keys) + step_seconds if all_bucket_keys else int(time.time())),
            "series": series,
            "p95": p95_points,
        }

    def top_endpoints(
        self,
        range_seconds: int,
        limit: int,
        sort_by: str,
        scope_id: str | None = None,
    ) -> list[dict]:
        """Топ маршрутов по p95 | error_rate | rps."""
        recent = self._select_recent(range_seconds, scope_id)
        if not recent:
            return []

        agg: dict[str, list[RequestRecord]] = defaultdict(list)
        for r in recent:
            agg[r.route].append(r)

        rows: list[tuple[str, float, float, float, int]] = []
        for route, rs in agg.items():
            count = len(rs)
            errors = sum(1 for r in rs if r.status_code >= 400)
            p95 = _percentile([r.duration_ms for r in rs], 0.95)
            rps = count / range_seconds
            err_rate = errors / count if count else 0.0
            rows.append((route, p95, err_rate, rps, count))

        if sort_by == "p95":
            rows.sort(key=lambda x: x[1], reverse=True)
        elif sort_by == "error_rate":
            rows.sort(key=lambda x: x[2], reverse=True)
        else:  # rps
            rows.sort(key=lambda x: x[3], reverse=True)

        out = []
        for route, p95, err_rate, rps, count in rows[: max(limit, 1)]:
            out.append(
                {
                    "route": route,
                    "p95": p95,
                    "error_rate": err_rate,
                    "rps": rps,
                    "count": count,
                }
            )
        return out

    def recent_errors(self, limit: int = 100, scope_id: str | None = None) -> list[dict]:
        """Последние ошибки (4xx/5xx)."""
        with self._lock:
            # идем с конца дека
            it: Iterable[RequestRecord] = reversed(self._records)
            out: list[dict] = []
            for r in it:
                if r.status_code >= 400 and (scope_id is None or r.scope_id == scope_id):
                    out.append(
                        {
                            "ts": int(r.ts),
                            "method": r.method,
                            "route": r.route,
                            "status_code": r.status_code,
                            "duration_ms": r.duration_ms,
                        }
                    )
                    if len(out) >= limit:
                        break
        return out

    def prometheus(self) -> str:
        """Render collected HTTP metrics in Prometheus text format."""
        with self._lock:
            records = list(self._records)
        lines: list[str] = []
        lines.append("# HELP http_requests_total Total HTTP requests")
        lines.append("# TYPE http_requests_total counter")
        count_map: dict[tuple[str, str, str, int], int] = defaultdict(int)
        duration_map: dict[tuple[str, str, str], list[int]] = defaultdict(list)
        for r in records:
            acc = r.scope_id or "unknown"
            count_map[(acc, r.method, r.route, r.status_code)] += 1
            duration_map[(acc, r.method, r.route)].append(r.duration_ms)
        for (acc, method, route, status), cnt in count_map.items():
            lines.append(
                f'http_requests_total{{scope="{acc}",method="{method}",path="{route}",status="{status}"}} {cnt}'
            )

        # Legacy /admin/nodes metrics removed after nodes deprecation

        lines.append(
            "# HELP domain_request_errors_total Total request errors by domain and status class"
        )
        lines.append("# TYPE domain_request_errors_total counter")
        domain_error_map: dict[tuple[str, str], int] = defaultdict(int)
        for r in records:
            for domain in ("users", "nodes", "nodes"):
                if r.route.startswith(f"/{domain}"):
                    if 400 <= r.status_code < 500:
                        domain_error_map[(domain, "4xx")] += 1
                    elif r.status_code >= 500:
                        domain_error_map[(domain, "5xx")] += 1
        for (domain, cls), cnt in domain_error_map.items():
            lines.append(f'domain_request_errors_total{{domain="{domain}",status="{cls}"}} {cnt}')

        lines.append("# HELP http_request_duration_ms Request duration milliseconds")
        lines.append("# TYPE http_request_duration_ms histogram")
        buckets = [5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000]
        for (acc, method, route), values in duration_map.items():
            values_sorted = sorted(values)
            for b in buckets:
                count = sum(1 for v in values_sorted if v <= b)
                lines.append(
                    f'http_request_duration_ms_bucket{{le="{b}",scope="{acc}",method="{method}",path="{route}"}} {count}'
                )
            lines.append(
                f'http_request_duration_ms_bucket{{le="+Inf",scope="{acc}",method="{method}",path="{route}"}} {len(values_sorted)}'
            )
            lines.append(
                f'http_request_duration_ms_count{{scope="{acc}",method="{method}",path="{route}"}} {len(values_sorted)}'
            )
        lines.append(
            f'http_request_duration_ms_sum{{scope="{acc}",method="{method}",path="{route}"}} {sum(values_sorted)}'
        )
        return "\n".join(lines) + "\n"

    def render_summary(self, range_seconds: int, output: str = "json") -> str:
        """Return aggregated metrics in either JSON or pretty text form."""
        data = self.summary(range_seconds)
        if output == "pretty":
            return "\n".join(f"{k}: {v}" for k, v in data.items()) + "\n"
        return json.dumps(data)


metrics_storage = MetricsStorage()

