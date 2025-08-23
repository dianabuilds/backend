from __future__ import annotations

import time
import os
from dataclasses import dataclass
from typing import Dict


@dataclass
class _State:
    failures: int = 0
    opened_until: float = 0.0  # unix ts, 0 — закрыт


class LLMCircuitBreaker:
    def __init__(self) -> None:
        self._states: Dict[str, _State] = {}

    def _get(self, provider: str) -> _State:
        return self._states.setdefault(provider, _State())

    def allow(self, provider: str) -> bool:
        st = self._get(provider)
        now = time.time()
        return st.opened_until <= now

    def on_success(self, provider: str) -> None:
        st = self._get(provider)
        st.failures = 0
        st.opened_until = 0.0

    def on_failure(self, provider: str) -> None:
        st = self._get(provider)
        st.failures += 1
        threshold = int(os.getenv("AI_CB_FAIL_THRESHOLD", "3"))
        cooldown = float(os.getenv("AI_CB_COOLDOWN_SEC", "30"))
        if st.failures >= max(threshold, 1):
            st.opened_until = time.time() + max(cooldown, 1.0)


llm_circuit = LLMCircuitBreaker()
