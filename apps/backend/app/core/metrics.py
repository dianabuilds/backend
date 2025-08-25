import json
import math
import threading
import time
from collections import defaultdict, deque
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Deque, Dict, List, Tuple


@dataclass
class RequestRecord:
    ts: float
    duration_ms: int
    status_code: int
    method: str
    route: str  # шаблон маршрута, либо фактический путь, если шаблон недоступен
    workspace_id: str | None


_transition_lock = threading.Lock()
_route_latencies: Deque[int] = deque(maxlen=1000)
_repeat_rates: Deque[float] = deque(maxlen=1000)
_route_lengths: Dict[str, Deque[int]] = defaultdict(lambda: deque(maxlen=1000))
_tag_entropies: Dict[str, Deque[float]] = defaultdict(lambda: deque(maxlen=1000))
_transition_counts: Dict[str, int] = defaultdict(int)
_no_route_counts: Dict[str, int] = defaultdict(int)
_fallback_used_counts: Dict[str, int] = defaultdict(int)
_preview_route_lengths: Dict[str, Deque[int]] = defaultdict(lambda: deque(maxlen=1000))
_preview_transition_counts: Dict[str, int] = defaultdict(int)
_preview_no_route_counts: Dict[str, int] = defaultdict(int)


def record_route_latency_ms(value: float) -> None:
    with _transition_lock:
        _route_latencies.append(int(value))


def record_repeat_rate(rate: float) -> None:
    with _transition_lock:
        _repeat_rates.append(rate)


def record_route_length(
    length: int, workspace_id: str | None, preview: bool = False
) -> None:
    ws = workspace_id or "unknown"
    with _transition_lock:
        if preview:
            _preview_route_lengths[ws].append(length)
            _preview_transition_counts[ws] += 1
        else:
            _route_lengths[ws].append(length)
            _transition_counts[ws] += 1


def record_tag_entropy(entropy: float, workspace_id: str | None) -> None:
    ws = workspace_id or "unknown"
    with _transition_lock:
        _tag_entropies[ws].append(entropy)


def record_no_route(workspace_id: str | None, preview: bool = False) -> None:
    ws = workspace_id or "unknown"
    with _transition_lock:
        if preview:
            _preview_no_route_counts[ws] += 1
            _preview_transition_counts[ws] += 1
        else:
            _no_route_counts[ws] += 1
            _transition_counts[ws] += 1


def record_fallback_used(workspace_id: str | None) -> None:
    ws = workspace_id or "unknown"
    with _transition_lock:
        _fallback_used_counts[ws] += 1


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


def _percentile(values: List[int], p: float) -> float:
    if not values:
        return 0.0
    values_sorted = sorted(values)
    k = max(int(math.ceil(p * len(values_sorted))) - 1, 0)
    return float(values_sorted[k])


class MetricsStorage:
    """Simple in-memory storage for HTTP request metrics."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records: Deque[RequestRecord] = deque()

    def record(
        self,
        duration_ms: int,
        status_code: int,
        method: str,
        route: str,
        workspace_id: str | None = None,
    ) -> None:
        now = time.time()
        with self._lock:
            self._records.append(
                RequestRecord(
                    now, duration_ms, status_code, method, route, workspace_id
                )
            )
            # Храним не более 24 часов
            cutoff = now - 24 * 3600
            while self._records and self._records[0].ts < cutoff:
                self._records.popleft()

    def reset(self) -> None:
        with self._lock:
            self._records.clear()

    def _select_recent(self, range_seconds: int) -> List[RequestRecord]:
        now = time.time()
        cutoff = now - range_seconds
        with self._lock:
            return [r for r in self._records if r.ts >= cutoff]

    def summary(self, range_seconds: int) -> dict:
        recent = self._select_recent(range_seconds)
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

    def timeseries(self, range_seconds: int, step_seconds: int) -> dict:
        """Вернуть таймсерии: counts per status class и p95 latency по бакетам."""
        if step_seconds <= 0:
            step_seconds = 60
        recent = self._select_recent(range_seconds)
        if not recent:
            return {
                "step": step_seconds,
                "from": int(time.time()) - range_seconds,
                "to": int(time.time()),
                "series": [],
                "p95": [],
            }

        buckets: Dict[int, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        durations: Dict[int, List[int]] = defaultdict(list)

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
            points = [
                {"ts": b, "value": buckets[b].get(cls, 0)} for b in all_bucket_keys
            ]
            series.append({"name": cls, "points": points})
        # p95
        p95_points = [
            {"ts": b, "value": _percentile(durations[b], 0.95)} for b in all_bucket_keys
        ]

        return {
            "step": step_seconds,
            "from": (
                min(all_bucket_keys)
                if all_bucket_keys
                else int(time.time()) - range_seconds
            ),
            "to": (
                max(all_bucket_keys) + step_seconds
                if all_bucket_keys
                else int(time.time())
            ),
            "series": series,
            "p95": p95_points,
        }

    def top_endpoints(self, range_seconds: int, limit: int, sort_by: str) -> List[dict]:
        """Топ маршрутов по p95 | error_rate | rps."""
        recent = self._select_recent(range_seconds)
        if not recent:
            return []

        agg: Dict[str, List[RequestRecord]] = defaultdict(list)
        for r in recent:
            agg[r.route].append(r)

        rows: List[Tuple[str, float, float, float, int]] = []
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

    def recent_errors(self, limit: int = 100) -> List[dict]:
        """Последние ошибки (4xx/5xx)."""
        with self._lock:
            # идем с конца дека
            it: Iterable[RequestRecord] = reversed(self._records)
            out: List[dict] = []
            for r in it:
                if r.status_code >= 400:
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
        """Render collected metrics in Prometheus text format."""
        with self._lock:
            records = list(self._records)
        lines: List[str] = []
        lines.append("# HELP http_requests_total Total HTTP requests")
        lines.append("# TYPE http_requests_total counter")
        count_map: Dict[Tuple[str, str, str, int], int] = defaultdict(int)
        duration_map: Dict[Tuple[str, str, str], List[int]] = defaultdict(list)
        for r in records:
            ws = r.workspace_id or "unknown"
            count_map[(ws, r.method, r.route, r.status_code)] += 1
            duration_map[(ws, r.method, r.route)].append(r.duration_ms)
        for (ws, method, route, status), cnt in count_map.items():
            lines.append(
                f'http_requests_total{{workspace="{ws}",method="{method}",path="{route}",status="{status}"}} {cnt}'
            )

        lines.append("# HELP http_request_duration_ms Request duration milliseconds")
        lines.append("# TYPE http_request_duration_ms histogram")
        buckets = [5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000]
        for (ws, method, route), values in duration_map.items():
            values_sorted = sorted(values)
            for b in buckets:
                count = sum(1 for v in values_sorted if v <= b)
                lines.append(
                    f'http_request_duration_ms_bucket{{le="{b}",workspace="{ws}",method="{method}",path="{route}"}} {count}'
                )
            lines.append(
                f'http_request_duration_ms_bucket{{le="+Inf",workspace="{ws}",method="{method}",path="{route}"}} {len(values_sorted)}'
            )
            lines.append(
                f'http_request_duration_ms_count{{workspace="{ws}",method="{method}",path="{route}"}} {len(values_sorted)}'
            )
            lines.append(
                f'http_request_duration_ms_sum{{workspace="{ws}",method="{method}",path="{route}"}} {sum(values_sorted)}'
            )
        with _transition_lock:
            lat = list(_route_latencies)
            rates = list(_repeat_rates)
            lengths = {ws: list(v) for ws, v in _route_lengths.items()}
            entropies = {ws: list(v) for ws, v in _tag_entropies.items()}
            totals = dict(_transition_counts)
            no_routes = dict(_no_route_counts)
            fallbacks = dict(_fallback_used_counts)
            prev_lengths = {ws: list(v) for ws, v in _preview_route_lengths.items()}
            prev_totals = dict(_preview_transition_counts)
            prev_no_routes = dict(_preview_no_route_counts)
        lines.append("# HELP route_latency_ms Route latency milliseconds")
        lines.append("# TYPE route_latency_ms summary")
        if lat:
            avg = sum(lat) / len(lat)
            p95 = _percentile(lat, 0.95)
            lines.append(f"route_latency_ms_avg {avg}")
            lines.append(f"route_latency_ms_p95 {p95}")
        else:
            lines.append("route_latency_ms_avg 0")
            lines.append("route_latency_ms_p95 0")
        lines.append("# HELP repeat_rate Repeat rate of filtered candidates")
        lines.append("# TYPE repeat_rate gauge")
        if rates:
            lines.append(f"repeat_rate {sum(rates) / len(rates)}")
        else:
            lines.append("repeat_rate 0")
        lines.append(
            "# HELP transition_no_route_percent Percentage of transitions without route"
        )
        lines.append("# TYPE transition_no_route_percent gauge")
        for ws, cnt in no_routes.items():
            total = totals.get(ws, 0)
            pct = (cnt / total * 100) if total else 0.0
            lines.append(f'transition_no_route_percent{{workspace="{ws}"}} {pct}')
        lines.append(
            "# HELP transition_preview_no_route_percent Percentage of preview transitions without route",
        )
        lines.append("# TYPE transition_preview_no_route_percent gauge")
        for ws, cnt in prev_no_routes.items():
            total = prev_totals.get(ws, 0)
            pct = (cnt / total * 100) if total else 0.0
            lines.append(
                f'transition_preview_no_route_percent{{workspace="{ws}"}} {pct}'
            )
        lines.append(
            "# HELP transition_fallback_used_percent Percentage of transitions using fallback"
        )
        lines.append("# TYPE transition_fallback_used_percent gauge")
        for ws, cnt in fallbacks.items():
            total = totals.get(ws, 0)
            pct = (cnt / total * 100) if total else 0.0
            lines.append(f'transition_fallback_used_percent{{workspace="{ws}"}} {pct}')
        lines.append("# HELP tag_entropy_avg Average tag entropy per workspace")
        lines.append("# TYPE tag_entropy_avg gauge")
        for ws, vals in entropies.items():
            avg = sum(vals) / len(vals) if vals else 0.0
            lines.append(f'tag_entropy_avg{{workspace="{ws}"}} {avg}')
        lines.append("# HELP route_length Route length")
        lines.append("# TYPE route_length summary")
        for ws, vals in lengths.items():
            avg = sum(vals) / len(vals) if vals else 0.0
            p95 = _percentile(vals, 0.95) if vals else 0.0
            lines.append(f'route_length_avg{{workspace="{ws}"}} {avg}')
            lines.append(f'route_length_p95{{workspace="{ws}"}} {p95}')
        lines.append("# HELP preview_route_length Route length in preview")
        lines.append("# TYPE preview_route_length summary")
        for ws, vals in prev_lengths.items():
            avg = sum(vals) / len(vals) if vals else 0.0
            p95 = _percentile(vals, 0.95) if vals else 0.0
            lines.append(f'preview_route_length_avg{{workspace="{ws}"}} {avg}')
            lines.append(f'preview_route_length_p95{{workspace="{ws}"}} {p95}')
        return "\n".join(lines) + "\n"

    def render_summary(self, range_seconds: int, output: str = "json") -> str:
        """Return aggregated metrics in either JSON or pretty text form."""
        data = self.summary(range_seconds)
        if output == "pretty":
            return "\n".join(f"{k}: {v}" for k, v in data.items()) + "\n"
        return json.dumps(data)


def transition_stats() -> Dict[str, dict]:
    with _transition_lock:
        out: Dict[str, dict] = {}
        for ws in _transition_counts.keys():
            lengths = list(_route_lengths.get(ws, []))
            ents = list(_tag_entropies.get(ws, []))
            total = _transition_counts.get(ws, 0)
            no_r = _no_route_counts.get(ws, 0)
            fb = _fallback_used_counts.get(ws, 0)
            out[ws] = {
                "route_length_avg": sum(lengths) / len(lengths) if lengths else 0.0,
                "route_length_p95": _percentile(lengths, 0.95) if lengths else 0.0,
                "tag_entropy_avg": sum(ents) / len(ents) if ents else 0.0,
                "no_route_percent": (no_r / total * 100) if total else 0.0,
                "fallback_used_percent": (fb / total * 100) if total else 0.0,
            }
        return out


metrics_storage = MetricsStorage()
