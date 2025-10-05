from __future__ import annotations

from domains.platform.telemetry.ports.llm_metrics_port import (
    ILLMMetricsSink,
    LLMCallLabels,
)


class InMemoryLLMMetricsSink(ILLMMetricsSink):
    def __init__(self) -> None:
        self.counters: dict[tuple[str, str, str, str], int] = {}
        self.latency_sum: dict[tuple[str, str, str], float] = {}
        self.latency_count: dict[tuple[str, str, str], int] = {}
        self.tokens_sum: dict[tuple[str, str, str, str], int] = {}
        self.cost_sum: dict[tuple[str, str, str], float] = {}

    def _k(self, metric: str, labels: LLMCallLabels) -> tuple[str, str, str, str]:
        return (metric, labels.provider, labels.model, labels.stage or "unknown")

    def inc(self, metric: str, labels: LLMCallLabels, by: int = 1) -> None:
        self.counters[self._k(metric, labels)] = (
            self.counters.get(self._k(metric, labels), 0) + by
        )

    def observe_latency(self, labels: LLMCallLabels, ms: float) -> None:
        key = (labels.provider, labels.model, labels.stage or "unknown")
        self.latency_sum[key] = self.latency_sum.get(key, 0.0) + float(ms)
        self.latency_count[key] = self.latency_count.get(key, 0) + 1

    def observe_tokens(
        self, labels: LLMCallLabels, prompt: int, completion: int
    ) -> None:
        kpr = (labels.provider, labels.model, labels.stage or "unknown", "prompt")
        kco = (labels.provider, labels.model, labels.stage or "unknown", "completion")
        self.tokens_sum[kpr] = self.tokens_sum.get(kpr, 0) + int(prompt)
        self.tokens_sum[kco] = self.tokens_sum.get(kco, 0) + int(completion)

    def observe_cost(self, labels: LLMCallLabels, cost: float) -> None:
        key = (labels.provider, labels.model, labels.stage or "unknown")
        self.cost_sum[key] = self.cost_sum.get(key, 0.0) + float(cost)

    def snapshot(self) -> dict:
        """JSON-friendly snapshot for admin UI consumption."""
        calls: list[dict[str, object]] = []
        for (metric, provider, model, stage), cnt in self.counters.items():
            calls.append(
                {
                    "type": metric,
                    "provider": provider,
                    "model": model,
                    "stage": stage,
                    "count": int(cnt),
                }
            )
        lat: list[dict[str, object]] = []
        for (provider, model, stage), s in self.latency_sum.items():
            c = self.latency_count.get((provider, model, stage), 1)
            lat.append(
                {
                    "provider": provider,
                    "model": model,
                    "stage": stage,
                    "avg_ms": (s / max(c, 1)),
                }
            )
        toks: list[dict[str, object]] = []
        for (provider, model, stage, t), s in self.tokens_sum.items():
            toks.append(
                {
                    "provider": provider,
                    "model": model,
                    "stage": stage,
                    "type": t,
                    "total": int(s),
                }
            )
        cost: list[dict[str, object]] = []
        for (provider, model, stage), s in self.cost_sum.items():
            cost.append(
                {
                    "provider": provider,
                    "model": model,
                    "stage": stage,
                    "total_usd": float(s),
                }
            )
        return {
            "calls": calls,
            "latency_avg_ms": lat,
            "tokens_total": toks,
            "cost_usd_total": cost,
        }

    def prometheus(self) -> str:
        lines = []
        lines.append("# HELP llm_calls_total Total LLM calls")
        lines.append("# TYPE llm_calls_total counter")
        for (metric, provider, model, stage), cnt in self.counters.items():
            lines.append(
                f'llm_calls_total{{type="{metric}",provider="{provider}",model="{model}",stage="{stage}"}} {cnt}'
            )
        lines.append("# HELP llm_latency_ms Average LLM latency (ms)")
        lines.append("# TYPE llm_latency_ms gauge")
        for (provider, model, stage), s in self.latency_sum.items():
            c = self.latency_count.get((provider, model, stage), 1)
            avg = s / max(c, 1)
            lines.append(
                f'llm_latency_ms{{provider="{provider}",model="{model}",stage="{stage}"}} {avg}'
            )
        lines.append("# HELP llm_tokens_total Total tokens by type")
        lines.append("# TYPE llm_tokens_total counter")
        for (provider, model, stage, t), s in self.tokens_sum.items():
            lines.append(
                f'llm_tokens_total{{provider="{provider}",model="{model}",stage="{stage}",type="{t}"}} {s}'
            )
        lines.append("# HELP llm_cost_usd_total Total cost (USD)")
        lines.append("# TYPE llm_cost_usd_total counter")
        for (provider, model, stage), s in self.cost_sum.items():
            lines.append(
                f'llm_cost_usd_total{{provider="{provider}",model="{model}",stage="{stage}"}} {s}'
            )
        return "\n".join(lines) + "\n"


__all__ = ["InMemoryLLMMetricsSink"]
