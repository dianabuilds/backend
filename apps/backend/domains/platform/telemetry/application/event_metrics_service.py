from __future__ import annotations

import threading


class EventMetrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        # event -> count
        self._counters: dict[str, int] = {}
        # event -> handler -> {"success": int, "failure": int}
        self._handler_counts: dict[str, dict[str, dict[str, int]]] = {}
        # event -> handler -> total duration ms
        self._handler_time_sum: dict[str, dict[str, float]] = {}
        # event -> handler -> count
        self._handler_time_count: dict[str, dict[str, int]] = {}

    def inc(self, event: str) -> None:
        with self._lock:
            self._counters[event] = self._counters.get(event, 0) + 1

    def record_handler(self, event: str, handler: str, success: bool, duration_ms: float) -> None:
        status = "success" if success else "failure"
        with self._lock:
            hmap = self._handler_counts.setdefault(event, {}).setdefault(handler, {})
            hmap[status] = hmap.get(status, 0) + 1
            tmap = self._handler_time_sum.setdefault(event, {})
            tmap[handler] = tmap.get(handler, 0.0) + duration_ms
            cmap = self._handler_time_count.setdefault(event, {})
            cmap[handler] = cmap.get(handler, 0) + 1

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()
            self._handler_counts.clear()
            self._handler_time_sum.clear()
            self._handler_time_count.clear()

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return dict(self._counters)

    def handler_snapshot(self) -> list[dict[str, object]]:
        """Aggregate handler stats with success/failure counts and avg duration."""
        rows: list[dict[str, object]] = []
        with self._lock:
            for ev, hmap in self._handler_counts.items():
                for handler, smap in hmap.items():
                    success = int(smap.get("success", 0))
                    failure = int(smap.get("failure", 0))
                    total = success + failure
                    t_sum = float(self._handler_time_sum.get(ev, {}).get(handler, 0.0))
                    t_cnt = int(self._handler_time_count.get(ev, {}).get(handler, 0))
                    avg_ms = (t_sum / t_cnt) if t_cnt else 0.0
                    rows.append(
                        {
                            "event": ev,
                            "handler": handler,
                            "success": success,
                            "failure": failure,
                            "total": total,
                            "avg_ms": avg_ms,
                        }
                    )
        return rows

    def prometheus(self) -> str:
        lines: list[str] = []
        lines.append("# HELP app_events_total Total domain events")
        lines.append("# TYPE app_events_total counter")
        with self._lock:
            for ev, cnt in self._counters.items():
                lines.append(f'app_events_total{{event="{ev}"}} {cnt}')
            lines.append("# HELP app_event_handler_calls_total Event handler calls")
            lines.append("# TYPE app_event_handler_calls_total counter")
            for ev, hmap in self._handler_counts.items():
                for handler, smap in hmap.items():
                    for status, cnt in smap.items():
                        call_line = (
                            "app_event_handler_calls_total"
                            f'{{event="{ev}",handler="{handler}",status="{status}"}} '
                            f"{cnt}"
                        )
                        lines.append(call_line)
            lines.append(
                "# HELP app_event_handler_duration_ms Event handler duration in milliseconds"
            )
            lines.append("# TYPE app_event_handler_duration_ms summary")
            for ev, tmap in self._handler_time_sum.items():
                for handler, total in tmap.items():
                    count = self._handler_time_count.get(ev, {}).get(handler, 0)
                    sum_line = (
                        "app_event_handler_duration_ms_sum"
                        f'{{event="{ev}",handler="{handler}"}} {total}'
                    )
                    lines.append(sum_line)
                    count_line = (
                        "app_event_handler_duration_ms_count"
                        f'{{event="{ev}",handler="{handler}"}} {count}'
                    )
                    lines.append(count_line)
        return "\n".join(lines) + "\n"


event_metrics = EventMetrics()

__all__ = ["event_metrics", "EventMetrics"]
