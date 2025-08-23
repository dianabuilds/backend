from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class GenerationStageLog:
    job_id: Any
    stage: str
    provider: str
    model: str
    prompt: str
    raw_response: str
    usage: Dict[str, int]
    cost: float
    status: str = "ok"
