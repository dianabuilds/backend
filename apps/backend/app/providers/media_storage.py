from __future__ import annotations

from typing import Protocol


class IMediaStorage(Protocol):
    async def save(self, path: str, data: bytes) -> str: ...


class FakeMediaStorage(IMediaStorage):
    async def save(self, path: str, data: bytes) -> str:
        return f"fake://{path}"


class SandboxMediaStorage(IMediaStorage):
    async def save(self, path: str, data: bytes) -> str:
        return f"sandbox://{path}"


class RealMediaStorage(IMediaStorage):
    async def save(self, path: str, data: bytes) -> str:
        return f"real://{path}"
