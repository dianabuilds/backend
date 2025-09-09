from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.referrals.application.ports.repository import IReferralsRepository
from app.domains.referrals.infrastructure.models.referral_models import ReferralCode
from app.domains.users.infrastructure.models.user import User


class ReferralsService:
    def __init__(self, repo: IReferralsRepository) -> None:
        self._repo = repo

    async def get_or_create_personal_code(self, db: AsyncSession, owner_user_id: UUID) -> ReferralCode:
        code = await self._repo.get_personal_code(owner_user_id)
        if code:
            return code
        # Try username-based deterministic code first
        user = await db.get(User, owner_user_id)
        base = (getattr(user, "username", None) or str(owner_user_id))[:16].lower()
        base = "".join(ch for ch in base if ch.isalnum() or ch in {".", "_"}).strip("._")
        guess = f"{base}" if base else None
        if guess:
            # ensure uniqueness across table
            existing = await self._repo.find_code(guess)
            if existing is None:
                return await self._repo.create_personal_code(owner_user_id, guess)
        # Fallback – generate unique random code
        # type: ignore[attr-defined]
        gen_code = await getattr(self._repo, "generate_unique_code")()  # provided by concrete repo
        return await self._repo.create_personal_code(owner_user_id, gen_code)

    async def process_signup_referral(
        self,
        db: AsyncSession,
        referral_code: str,
        referee_user_id: UUID,
        ip: str | None = None,
        ua: str | None = None,
    ) -> bool:
        # Locate active code
        code = await self._repo.find_code(referral_code)
        if not code:
            return False
        # Prevent self-referral
        if code.owner_user_id == referee_user_id:
            return False

        meta: dict[str, Any] = {}
        if ip:
            meta["ip"] = ip
        if ua:
            meta["ua"] = ua

        evt = await self._repo.record_signup(code=code, referee_user_id=referee_user_id, meta=meta)
        if not evt:
            return False
        return True


