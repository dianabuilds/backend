from __future__ import annotations

from domains.platform.telemetry.ports.llm_metrics_port import (
    ILLMMetricsSink,
    LLMCallLabels,
)


class LLMMetricsFacade:
    def __init__(self, sink: ILLMMetricsSink) -> None:
        self._sink = sink

    def inc(self, metric: str, labels: LLMCallLabels, by: int = 1) -> None:
        self._sink.inc(metric, labels, by)

    def observe_latency(self, labels: LLMCallLabels, ms: float) -> None:
        self._sink.observe_latency(labels, ms)

    def observe_tokens(self, labels: LLMCallLabels, prompt: int, completion: int) -> None:
        self._sink.observe_tokens(labels, prompt, completion)

    def observe_cost(self, labels: LLMCallLabels, cost: float) -> None:
        self._sink.observe_cost(labels, cost)

    def prometheus(self) -> str:
        return self._sink.prometheus()

    def snapshot(self) -> dict:
        """Lightweight JSON snapshot for admin UI."""
        snap = getattr(self._sink, "snapshot", None)
        if callable(snap):
            return snap()  # type: ignore[return-value]
        return {
            "calls": [],
            "latency_avg_ms": [],
            "tokens_total": [],
            "cost_usd_total": [],
        }


__all__ = ["LLMMetricsFacade"]
