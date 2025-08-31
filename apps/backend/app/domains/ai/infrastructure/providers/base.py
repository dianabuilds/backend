from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


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
    latency: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass
class LLMResult:
    text: str
    model: str
    usage: LLMUsage
    raw: dict[str, Any] | None = None


class LLMProvider(Protocol):
    name: str

    async def complete(
        self,
        *,
        model: str,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        timeout: float = 30.0,
        json_mode: bool = False,
    ) -> LLMResult: ...

    async def count_tokens(
        self,
        *,
        model: str,
        prompt: str,
        system: str | None = None,
    ) -> int | None:
        """Return number of tokens in the prompt if provider supports it."""
        ...
