from __future__ import annotations

from typing import Protocol


class IAIProvider(Protocol):
    async def generate(self, prompt: str) -> str: ...


class FakeAIProvider(IAIProvider):
    async def generate(self, prompt: str) -> str:
        return f"fake:{prompt}"


class SandboxAIProvider(IAIProvider):
    async def generate(self, prompt: str) -> str:
        return f"sandbox:{prompt}"


class RealAIProvider(IAIProvider):
    async def generate(self, prompt: str) -> str:
        return f"real:{prompt}"
