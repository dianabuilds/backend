from __future__ import annotations

from typing import Protocol


class IEmail(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...


class FakeEmail(IEmail):
    async def send(self, to: str, subject: str, body: str) -> None:
        return None


class SandboxEmail(IEmail):
    async def send(self, to: str, subject: str, body: str) -> None:
        return None


class RealEmail(IEmail):
    async def send(self, to: str, subject: str, body: str) -> None:
        return None
