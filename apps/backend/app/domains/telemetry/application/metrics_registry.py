from __future__ import annotations

from app.domains.telemetry.application.llm_metrics_facade import LLMMetricsFacade
from app.domains.telemetry.infrastructure.llm_metrics_adapter import (
    InMemoryLLMMetricsSink,
)

# Единый для процесса экземпляр метрик LLM
llm_metrics = LLMMetricsFacade(InMemoryLLMMetricsSink())

__all__ = ["llm_metrics"]
