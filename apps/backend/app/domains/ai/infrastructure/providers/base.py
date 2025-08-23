from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol


class LLMError(Exception):
    pass


class LLMRateLimit(LLMError):
    pass


class LLMServerError(LLMError):
    pass


@dataclass
class LLMUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass
class LLMResult:
    text: str
    model: str
    usage: LLMUsage
    raw: Optional[Dict[str, Any]] = None


class LLMProvider(Protocol):
    name: str

    async def complete(
        self,
        *,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        timeout: float = 30.0,
        json_mode: bool = False,
    ) -> LLMResult:
        ...
