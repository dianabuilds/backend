from __future__ import annotations

from domains.product.ai.application.ports import Provider


class FakeProvider(Provider):
    async def generate(self, prompt: str) -> str:
        return f"fake:{prompt}"
