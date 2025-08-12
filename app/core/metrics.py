import math
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, List


@dataclass
class RequestRecord:
    ts: float
    duration_ms: int
    status_code: int


class MetricsStorage:
    """Simple in-memory storage for HTTP request metrics."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records: Deque[RequestRecord] = deque()

    def record(self, duration_ms: int, status_code: int) -> None:
        now = time.time()
        with self._lock:
            self._records.append(RequestRecord(now, duration_ms, status_code))
            cutoff = now - 24 * 3600
            while self._records and self._records[0].ts < cutoff:
                self._records.popleft()

    def reset(self) -> None:
        with self._lock:
            self._records.clear()

    def summary(self, range_seconds: int) -> dict:
        now = time.time()
        cutoff = now - range_seconds
        with self._lock:
            recent: List[RequestRecord] = [r for r in self._records if r.ts >= cutoff]

        total = len(recent)
        if total == 0:
            return {
                "rps": 0.0,
                "error_rate": 0.0,
                "p95_latency": 0.0,
                "count_429": 0,
            }

        errors = sum(1 for r in recent if r.status_code >= 400)
        sorted_durations = sorted(r.duration_ms for r in recent)
        index = max(int(math.ceil(0.95 * total)) - 1, 0)
        p95 = sorted_durations[index]
        count_429 = sum(1 for r in recent if r.status_code == 429)
        return {
            "rps": total / range_seconds,
            "error_rate": errors / total,
            "p95_latency": p95,
            "count_429": count_429,
        }


metrics_storage = MetricsStorage()
