from __future__ import annotations

from typing import Protocol


class IPayments(Protocol):
    async def charge(self, amount: int) -> bool: ...


class FakePayments(IPayments):
    async def charge(self, amount: int) -> bool:
        return True


class SandboxPayments(IPayments):
    async def charge(self, amount: int) -> bool:
        return True


class RealPayments(IPayments):
    async def charge(self, amount: int) -> bool:
        return True
