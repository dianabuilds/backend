from __future__ import annotations

from datetime import datetime
from secrets import token_urlsafe
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.referrals.application.ports.repository import IReferralsRepository
from app.domains.referrals.infrastructure.models.referral_models import ReferralCode, ReferralEvent


class ReferralsRepository(IReferralsRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_personal_code(self, owner_user_id: UUID) -> ReferralCode | None:
        res = await self._db.execute(
            select(ReferralCode).where(
                ReferralCode.owner_user_id == owner_user_id,
            )
        )
        return res.scalars().first()

    async def create_personal_code(self, owner_user_id: UUID, code: str) -> ReferralCode:
        item = ReferralCode(owner_user_id=owner_user_id, code=code, active=True)
        self._db.add(item)
        await self._db.flush()
        await self._db.refresh(item)
        return item

    async def _code_exists(self, code: str) -> bool:
        res = await self._db.execute(select(ReferralCode.id).where(ReferralCode.code == code))
        return res.scalar() is not None

    async def find_code(self, code: str) -> ReferralCode | None:
        res = await self._db.execute(
            select(ReferralCode).where(ReferralCode.code == code, ReferralCode.active.is_(True))
        )
        return res.scalars().first()

    async def record_signup(
        self, *, code: ReferralCode, referee_user_id: UUID, meta: dict | None = None
    ) -> ReferralEvent | None:
        # One signup per referee globally
        exists = await self._db.execute(
            select(ReferralEvent.id).where(
                ReferralEvent.referee_user_id == referee_user_id,
                ReferralEvent.event_type == "signup",
            )
        )
        if exists.scalar() is not None:
            return None
        evt = ReferralEvent(
            code_id=code.id,
            code=code.code,
            referrer_user_id=code.owner_user_id,
            referee_user_id=referee_user_id,
            event_type="signup",
            occurred_at=datetime.utcnow(),
            meta=(meta or {}),
        )
        self._db.add(evt)
        # increment uses_count
        code.uses_count = int(code.uses_count or 0) + 1
        await self._db.flush()
        await self._db.refresh(evt)
        return evt

    async def count_signups(self, referrer_user_id: UUID) -> int:
        res = await self._db.execute(
            select(func.count(ReferralEvent.id)).where(
                ReferralEvent.referrer_user_id == referrer_user_id,
                ReferralEvent.event_type == "signup",
            )
        )
        return int(res.scalar() or 0)

    async def list_codes(
        self,
        owner_user_id: UUID | None = None,
        active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ReferralCode]:
        stmt = select(ReferralCode)
        if owner_user_id is not None:
            stmt = stmt.where(ReferralCode.owner_user_id == owner_user_id)
        if active is not None:
            stmt = stmt.where(ReferralCode.active.is_(bool(active)))
        stmt = stmt.order_by(ReferralCode.created_at.desc()).limit(limit).offset(offset)
        res = await self._db.execute(stmt)
        return list(res.scalars().all())

    async def list_events(
        self, referrer_user_id: UUID | None = None, limit: int = 50, offset: int = 0
    ) -> list[ReferralEvent]:
        stmt = select(ReferralEvent)
        if referrer_user_id is not None:
            stmt = stmt.where(ReferralEvent.referrer_user_id == referrer_user_id)
        stmt = stmt.order_by(ReferralEvent.occurred_at.desc()).limit(limit).offset(offset)
        res = await self._db.execute(stmt)
        return list(res.scalars().all())

    async def generate_unique_code(self, prefix: str = "ref-") -> str:
        # Short, urlsafe, lowercased code
        for _ in range(10):
            candidate = (prefix + token_urlsafe(6)).replace("_", "").replace("-", "").lower()
            if not await self._code_exists(candidate):
                return candidate
        # Fallback – add timestamp fragment
        return (prefix + token_urlsafe(10)).replace("_", "").replace("-", "").lower()

    async def set_active(self, owner_user_id: UUID, active: bool) -> ReferralCode | None:
        code = await self.get_personal_code(owner_user_id)
        if code is None and active:
            # create a personal code if enabling
            gen = await self.generate_unique_code()
            code = await self.create_personal_code(owner_user_id, gen)
        if code is None:
            return None
        code.active = bool(active)
        await self._db.flush()
        await self._db.refresh(code)
        return code
