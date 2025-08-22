from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class LLMCallLabels:
    provider: str
    model: str
    stage: str  # beats|chapters|nodes|unknown


class ILLMMetricsSink(Protocol):
    def inc(self, metric: str, labels: LLMCallLabels, by: int = 1) -> None:  # pragma: no cover - контракт
        ...

    def observe_latency(self, labels: LLMCallLabels, ms: float) -> None:  # pragma: no cover - контракт
        ...

    def observe_tokens(self, labels: LLMCallLabels, prompt: int, completion: int) -> None:  # pragma: no cover
        ...

    def observe_cost(self, labels: LLMCallLabels, cost: float) -> None:  # pragma: no cover - контракт
        ...

    def prometheus(self) -> str:  # pragma: no cover - контракт
        ...
