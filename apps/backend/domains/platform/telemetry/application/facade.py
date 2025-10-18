from __future__ import annotations

from domains.platform.telemetry.application.metrics_registry import (
    llm_metrics as _llm_metrics,
)
from domains.platform.telemetry.ports.llm_metrics_port import (
    LLMCallLabels as _LLMCallLabels,
)

llm_metrics = _llm_metrics
LLMCallLabels = _LLMCallLabels

__all__ = ["llm_metrics", "LLMCallLabels"]
