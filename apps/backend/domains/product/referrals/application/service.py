from __future__ import annotations

import logging
from typing import Any

from domains.platform.events.application.publisher import OutboxError, OutboxPublisher
from domains.product.referrals.application.ports import Repo
from domains.product.referrals.domain.entities import ReferralCode

try:
    from redis.exceptions import RedisError  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    RedisError = Exception  # type: ignore[misc, assignment]


logger = logging.getLogger(__name__)

_OUTBOX_EXPECTED_ERRORS = (ValueError, RuntimeError, RedisError)


class ReferralsService:
    def __init__(self, repo: Repo, outbox: OutboxPublisher | None = None) -> None:
        self.repo = repo
        self.outbox = outbox

    def _safe_publish(self, topic: str, payload: dict[str, Any]) -> None:
        if not self.outbox:
            return
        extra = {"topic": topic, "referrer": payload.get("referrer_user_id")}
        try:
            self.outbox.publish(topic, payload)
        except _OUTBOX_EXPECTED_ERRORS as exc:
            logger.warning("referral_outbox_publish_failed", extra=extra, exc_info=exc)
        except Exception as exc:  # pragma: no cover - unexpected failure
            logger.exception(
                "referral_outbox_publish_unexpected", extra=extra, exc_info=exc
            )
            raise OutboxError(
                "referral_outbox_publish_unexpected", topic=topic
            ) from exc

    async def get_or_create_personal_code(self, owner_user_id: str) -> ReferralCode:
        code = await self.repo.get_personal_code(owner_user_id)
        if code:
            return code
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
        evt = await self.repo.record_signup(
            code=code, referee_user_id=referee_user_id, meta=meta
        )
        if evt:
            self._safe_publish(
                "referral.signup.recorded.v1",
                {
                    "code": code.code,
                    "referrer_user_id": code.owner_user_id,
                    "referee_user_id": referee_user_id,
                },
            )
        return bool(evt)

    async def set_active(self, owner_user_id: str, active: bool) -> ReferralCode | None:
        code = await self.repo.set_active(owner_user_id, active)
        if code:
            topic = (
                "referral.code.activated.v1"
                if active
                else "referral.code.deactivated.v1"
            )
            self._safe_publish(
                topic,
                {"owner_user_id": owner_user_id, "code": code.code},
            )
        return code
