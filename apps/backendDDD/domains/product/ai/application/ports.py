from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Provider(Protocol):
    async def generate(self, prompt: str) -> str: ...
