from __future__ import annotations

from typing import Any

from app.providers.ai import IAIProvider


class AIDomainProviderAdapter:
    """Adapter that wraps the monolith AI provider into DDD Provider port."""

    def __init__(self, provider: IAIProvider):
        self._provider = provider

    async def generate(self, prompt: str) -> str:
        return await self._provider.generate(prompt)

