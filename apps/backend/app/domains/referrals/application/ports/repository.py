from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.domains.referrals.infrastructure.models.referral_models import ReferralCode, ReferralEvent


class IReferralsRepository(Protocol):
    async def get_personal_code(self, owner_user_id: UUID) -> ReferralCode | None:  # pragma: no cover
        ...

    async def create_personal_code(self, owner_user_id: UUID, code: str) -> ReferralCode:  # pragma: no cover
        ...

    async def find_code(self, code: str) -> ReferralCode | None:  # pragma: no cover
        ...

    async def record_signup(self, *, code: ReferralCode, referee_user_id: UUID, meta: dict | None = None) -> ReferralEvent | None:  # pragma: no cover
        ...

    async def count_signups(self, referrer_user_id: UUID) -> int:  # pragma: no cover
        ...

    async def list_codes(self, owner_user_id: UUID | None = None, active: bool | None = None, limit: int = 50, offset: int = 0) -> list[ReferralCode]:  # pragma: no cover
        ...

    async def list_events(self, referrer_user_id: UUID | None = None, limit: int = 50, offset: int = 0) -> list[ReferralEvent]:  # pragma: no cover
        ...
