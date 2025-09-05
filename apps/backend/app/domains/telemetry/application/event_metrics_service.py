from __future__ import annotations

import threading


class EventMetrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        # event -> workspace -> count
        self._counters: dict[str, dict[str, int]] = {}
        # event -> handler -> {"success": int, "failure": int}
        self._handler_counts: dict[str, dict[str, dict[str, int]]] = {}
        # event -> handler -> total duration ms
        self._handler_time_sum: dict[str, dict[str, float]] = {}
        # event -> handler -> count
        self._handler_time_count: dict[str, dict[str, int]] = {}

    def inc(self, event: str, workspace_id: str | None) -> None:
        ws = workspace_id or "unknown"
        with self._lock:
            ev_map = self._counters.setdefault(event, {})
            ev_map[ws] = ev_map.get(ws, 0) + 1

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

    def snapshot(self) -> dict[str, dict[str, int]]:
        # return workspace -> events
        with self._lock:
            out: dict[str, dict[str, int]] = {}
            for ev, ws_map in self._counters.items():
                for ws, cnt in ws_map.items():
                    out.setdefault(ws, {})[ev] = cnt
            return out

    def prometheus(self) -> str:
        lines = []
        lines.append("# HELP app_events_total Total domain events")
        lines.append("# TYPE app_events_total counter")
        with self._lock:
            for ev, ws_map in self._counters.items():
                for ws, cnt in ws_map.items():
                    lines.append(f'app_events_total{{event="{ev}",workspace="{ws}"}} {cnt}')
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
                "# HELP app_event_handler_duration_ms " "Event handler duration in milliseconds"
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
