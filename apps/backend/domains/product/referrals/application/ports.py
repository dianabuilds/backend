from __future__ import annotations

from typing import Protocol, runtime_checkable

from domains.product.referrals.domain.entities import (
    ReferralCode,
    ReferralEvent,
)


@runtime_checkable
class Repo(Protocol):
    async def get_personal_code(self, owner_user_id: str) -> ReferralCode | None: ...
    async def create_personal_code(
        self, owner_user_id: str, code: str
    ) -> ReferralCode: ...
    async def find_code(self, code: str) -> ReferralCode | None: ...
    async def record_signup(
        self, *, code: ReferralCode, referee_user_id: str, meta: dict | None = None
    ) -> ReferralEvent | None: ...
    async def count_signups(self, referrer_user_id: str) -> int: ...
    async def list_codes(
        self, *, owner_user_id: str | None, active: bool | None, limit: int, offset: int
    ) -> list[ReferralCode]: ...
    async def list_events(
        self, *, referrer_user_id: str | None, limit: int, offset: int
    ) -> list[ReferralEvent]: ...
    async def generate_unique_code(self, prefix: str = "ref-") -> str: ...
    async def set_active(
        self, owner_user_id: str, active: bool
    ) -> ReferralCode | None: ...
