from __future__ import annotations

import threading
from collections import deque


class UXMetrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._first_save: deque[float] = deque(maxlen=1000)
        self._published_total = 0
        self._published_with_tags = 0
        self._save_next_total = 0

    def record_first_save(self, seconds: float) -> None:
        with self._lock:
            self._first_save.append(seconds)

    def record_publish(self, has_tags: bool) -> None:
        with self._lock:
            self._published_total += 1
            if has_tags:
                self._published_with_tags += 1

    def inc_save_next(self) -> None:
        with self._lock:
            self._save_next_total += 1

    def prometheus(self) -> str:
        with self._lock:
            avg = (
                sum(self._first_save) / len(self._first_save)
                if self._first_save
                else 0.0
            )
            ratio = (
                self._published_with_tags / self._published_total
                if self._published_total
                else 0.0
            )
            lines = [
                "# HELP app_ux_time_to_first_save_seconds_avg Average time to first save",
                "# TYPE app_ux_time_to_first_save_seconds_avg gauge",
                f"app_ux_time_to_first_save_seconds_avg {avg}",
                "# HELP app_ux_tagged_ratio Ratio of published nodes with tags",
                "# TYPE app_ux_tagged_ratio gauge",
                f"app_ux_tagged_ratio {ratio}",
                "# HELP app_ux_save_next_total Count of Save & Next actions",
                "# TYPE app_ux_save_next_total counter",
                f"app_ux_save_next_total {self._save_next_total}",
            ]
            return "\n".join(lines) + "\n"


ux_metrics = UXMetrics()

__all__ = ["ux_metrics", "UXMetrics"]
