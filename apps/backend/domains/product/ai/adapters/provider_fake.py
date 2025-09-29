from __future__ import annotations

from domains.product.ai.application.ports import Provider


class FakeProvider(Provider):
    async def generate(
        self,
        prompt: str,
        *,
        model: str | None = None,
        provider: str | None = None,
        model_id: str | None = None,
    ) -> str:
        return f"fake:{prompt}"
