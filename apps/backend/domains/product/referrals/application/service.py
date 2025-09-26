from __future__ import annotations

from typing import Any

from domains.platform.events.ports import OutboxPublisher
from domains.product.referrals.application.ports import Repo
from domains.product.referrals.domain.entities import ReferralCode


class ReferralsService:
    def __init__(self, repo: Repo, outbox: OutboxPublisher | None = None) -> None:
        self.repo = repo
        self.outbox = outbox

    async def get_or_create_personal_code(self, owner_user_id: str) -> ReferralCode:
        code = await self.repo.get_personal_code(owner_user_id)
        if code:
            return code
        # generate unique code
        gen = await self.repo.generate_unique_code()
        return await self.repo.create_personal_code(owner_user_id, gen)

    async def process_signup_referral(
        self,
        referral_code: str,
        referee_user_id: str,
        *,
        ip: str | None = None,
        ua: str | None = None,
    ) -> bool:
        code = await self.repo.find_code(referral_code)
        if not code:
            return False
        if code.owner_user_id == referee_user_id:
            return False
        meta: dict[str, Any] = {}
        if ip:
            meta["ip"] = ip
        if ua:
            meta["ua"] = ua
        evt = await self.repo.record_signup(code=code, referee_user_id=referee_user_id, meta=meta)
        try:
            if evt and self.outbox:
                self.outbox.publish(
                    "referral.signup.recorded.v1",
                    {
                        "code": code.code,
                        "referrer_user_id": code.owner_user_id,
                        "referee_user_id": referee_user_id,
                    },
                )
        except Exception:
            pass
        return bool(evt)

    async def set_active(self, owner_user_id: str, active: bool) -> ReferralCode | None:
        code = await self.repo.set_active(owner_user_id, active)
        try:
            if code and self.outbox:
                self.outbox.publish(
                    ("referral.code.activated.v1" if active else "referral.code.deactivated.v1"),
                    {"owner_user_id": owner_user_id, "code": code.code},
                )
        except Exception:
            pass
        return code
