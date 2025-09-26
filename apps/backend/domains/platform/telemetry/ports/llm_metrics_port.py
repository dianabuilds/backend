from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class LLMCallLabels:
    provider: str
    model: str
    stage: str  # beats|chapters|nodes|unknown


class ILLMMetricsSink(Protocol):
    def inc(self, metric: str, labels: LLMCallLabels, by: int = 1) -> None: ...

    def observe_latency(self, labels: LLMCallLabels, ms: float) -> None: ...

    def observe_tokens(self, labels: LLMCallLabels, prompt: int, completion: int) -> None: ...

    def observe_cost(self, labels: LLMCallLabels, cost: float) -> None: ...

    def prometheus(self) -> str: ...


__all__ = ["ILLMMetricsSink", "LLMCallLabels"]
