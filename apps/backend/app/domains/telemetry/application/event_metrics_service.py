from __future__ import annotations

import threading
from typing import Dict


class EventMetrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        # event -> workspace -> count
        self._counters: Dict[str, Dict[str, int]] = {}

    def inc(self, event: str, workspace_id: str | None) -> None:
        ws = workspace_id or "unknown"
        with self._lock:
            ev_map = self._counters.setdefault(event, {})
            ev_map[ws] = ev_map.get(ws, 0) + 1

    def snapshot(self) -> Dict[str, Dict[str, int]]:
        # return workspace -> events
        with self._lock:
            out: Dict[str, Dict[str, int]] = {}
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
                    lines.append(
                        f'app_events_total{{event="{ev}",workspace="{ws}"}} {cnt}'
                    )
        return "\n".join(lines) + "\n"


event_metrics = EventMetrics()

__all__ = ["event_metrics", "EventMetrics"]
