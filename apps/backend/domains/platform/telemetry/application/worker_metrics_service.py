from __future__ import annotations

from typing import Any


class WorkerMetrics:
    def __init__(self) -> None:
        self.counters: dict[str, int] = {"started": 0, "completed": 0, "failed": 0}
        self.duration_sum_ms: float = 0.0
        self.duration_count: int = 0
        self.cost_usd_total: float = 0.0
        self.tokens_prompt_total: int = 0
        self.tokens_completion_total: int = 0
        self.stage_counts: dict[str, int] = {}
        self.stage_duration_sum_ms: dict[str, float] = {}

    def inc(self, key: str, by: int = 1) -> None:
        self.counters[key] = self.counters.get(key, 0) + by

    def observe_duration(self, ms: float) -> None:
        self.duration_sum_ms += float(ms)
        self.duration_count += 1

    def observe_job(
        self, *, cost_usd: float, prompt_tokens: int, completion_tokens: int
    ) -> None:
        self.cost_usd_total += float(cost_usd)
        self.tokens_prompt_total += int(prompt_tokens)
        self.tokens_completion_total += int(completion_tokens)

    def observe_stage(self, stage: str, ms: float) -> None:
        s = stage or "unknown"
        self.stage_counts[s] = self.stage_counts.get(s, 0) + 1
        self.stage_duration_sum_ms[s] = self.stage_duration_sum_ms.get(s, 0.0) + float(
            ms
        )

    def snapshot(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "jobs": dict(self.counters),
            "job_avg_ms": (
                (self.duration_sum_ms / self.duration_count)
                if self.duration_count
                else 0.0
            ),
            "cost_usd_total": self.cost_usd_total,
            "tokens": {
                "prompt": self.tokens_prompt_total,
                "completion": self.tokens_completion_total,
            },
            "stages": {},
        }
        for k, cnt in self.stage_counts.items():
            ssum = self.stage_duration_sum_ms.get(k, 0.0)
            out["stages"][k] = {"count": cnt, "avg_ms": (ssum / cnt) if cnt else 0.0}
        return out

    def prometheus(self) -> str:
        lines = []
        lines.append("# HELP ai_worker_jobs_total Total AI generation jobs by status")
        lines.append("# TYPE ai_worker_jobs_total counter")
        for k, v in self.counters.items():
            lines.append(f'ai_worker_jobs_total{{status="{k}"}} {v}')
        avg = (
            (self.duration_sum_ms / self.duration_count) if self.duration_count else 0.0
        )
        lines.append("# HELP ai_worker_job_duration_ms_avg Average job duration (ms)")
        lines.append("# TYPE ai_worker_job_duration_ms_avg gauge")
        lines.append(f"ai_worker_job_duration_ms_avg {avg}")
        lines.append(
            "# HELP ai_worker_cost_usd_total Total cost of generated jobs (USD)"
        )
        lines.append("# TYPE ai_worker_cost_usd_total counter")
        lines.append(f"ai_worker_cost_usd_total {self.cost_usd_total}")
        lines.append("# HELP ai_worker_tokens_total Total tokens across jobs by type")
        lines.append("# TYPE ai_worker_tokens_total counter")
        lines.append(
            f'ai_worker_tokens_total{{type="prompt"}} {self.tokens_prompt_total}'
        )
        lines.append(
            f'ai_worker_tokens_total{{type="completion"}} {self.tokens_completion_total}'
        )
        lines.append("# HELP ai_worker_stage_avg_ms Average stage duration (ms)")
        lines.append("# TYPE ai_worker_stage_avg_ms gauge")
        for k, cnt in self.stage_counts.items():
            ssum = self.stage_duration_sum_ms.get(k, 0.0)
            avg_ms = (ssum / cnt) if cnt else 0.0
            lines.append(f'ai_worker_stage_avg_ms{{stage="{k}"}} {avg_ms}')
            lines.append(f'ai_worker_stage_total{{stage="{k}"}} {cnt}')
        return "\n".join(lines) + "\n"


worker_metrics = WorkerMetrics()

__all__ = ["worker_metrics", "WorkerMetrics"]
