from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from domains.platform.telemetry.application.metrics_registry import llm_metrics
from domains.platform.telemetry.application.worker_metrics_service import worker_metrics


def _safe_iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


@dataclass
class MetricsProbe:
    def worker_signals(
        self, collected_at: str
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        snapshot = worker_metrics.snapshot()
        jobs = snapshot.get("jobs", {}) or {}
        completed = int(jobs.get("completed", jobs.get("succeeded", 0)))
        failed = int(jobs.get("failed", 0))
        total = completed + failed
        failure_rate = (failed / total) if total else 0.0
        status = "healthy"
        if failure_rate >= 0.2:
            status = "critical"
        elif failure_rate >= 0.05:
            status = "warning"

        signal = {
            "id": "worker:aggregate",
            "label": "Workers",
            "status": status,
            "ok": failure_rate < 0.05,
            "avg_duration_ms": float(snapshot.get("job_avg_ms") or 0.0),
            "failure_rate": failure_rate,
            "jobs_completed": completed,
            "jobs_failed": failed,
            "last_heartbeat": collected_at,
            "hint": "Async workers delivering jobs.",
        }
        summary = {
            "worker_avg_ms": float(snapshot.get("job_avg_ms") or 0.0),
            "worker_failure_rate": failure_rate,
        }
        return [signal], summary

    def llm_signals(
        self, collected_at: str
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        snapshot = llm_metrics.snapshot()
        calls = snapshot.get("calls", []) or []
        success = sum(
            int(item.get("count", 0))
            for item in calls
            if str(item.get("type")) == "calls"
        )
        errors = sum(
            int(item.get("count", 0))
            for item in calls
            if str(item.get("type")) == "errors"
        )
        total = success + errors
        success_rate = (success / total) if total else 1.0
        status = "healthy"
        if success_rate < 0.8:
            status = "critical"
        elif success_rate < 0.95:
            status = "warning"

        latency_entries = snapshot.get("latency_avg_ms", []) or []
        avg_latency = 0.0
        if latency_entries:
            avg_latency = sum(
                float(item.get("avg_ms", 0.0)) for item in latency_entries
            ) / len(latency_entries)

        signal = {
            "id": "llm:providers",
            "label": "LLM providers",
            "status": status,
            "ok": success_rate >= 0.95,
            "success_rate": success_rate,
            "latency_ms": round(avg_latency, 2) if avg_latency else None,
            "total_calls": total,
            "error_count": errors,
            "last_heartbeat": collected_at,
            "hint": "Model registry and providers.",
        }
        summary = {"llm_success_rate": success_rate}
        return [signal], summary


__all__ = ["MetricsProbe"]
