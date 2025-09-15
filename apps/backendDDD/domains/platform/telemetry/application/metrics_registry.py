from __future__ import annotations

from apps.backendDDD.domains.platform.telemetry.adapters.llm_metrics_adapter import (
    InMemoryLLMMetricsSink,
)
from apps.backendDDD.domains.platform.telemetry.application.llm_metrics_facade import (
    LLMMetricsFacade,
)

llm_metrics = LLMMetricsFacade(InMemoryLLMMetricsSink())

__all__ = ["llm_metrics"]
