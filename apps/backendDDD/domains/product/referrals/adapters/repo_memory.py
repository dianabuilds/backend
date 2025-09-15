from __future__ import annotations

import uuid

from apps.backendDDD.domains.product.referrals.application.ports import Repo
from apps.backendDDD.domains.product.referrals.domain.entities import (
    ReferralCode,
    ReferralEvent,
)


def _uuid() -> str:
    return str(uuid.uuid4())


class MemoryReferralsRepo(Repo):
    def __init__(self) -> None:
        self._codes_by_user: dict[str, ReferralCode] = {}
        self._codes_by_code: dict[str, ReferralCode] = {}
        self._events: list[ReferralEvent] = []

    async def get_personal_code(self, owner_user_id: str) -> ReferralCode | None:
        return self._codes_by_user.get(str(owner_user_id))

    async def create_personal_code(self, owner_user_id: str, code: str) -> ReferralCode:
        item = ReferralCode(
            id=_uuid(),
            owner_user_id=str(owner_user_id),
            code=str(code),
            active=True,
            uses_count=0,
        )
        self._codes_by_user[str(owner_user_id)] = item
        self._codes_by_code[item.code] = item
        return item

    async def find_code(self, code: str) -> ReferralCode | None:
        c = self._codes_by_code.get(str(code))
        if c and c.active:
            return c
        return None

    async def record_signup(
        self, *, code: ReferralCode, referee_user_id: str, meta: dict | None = None
    ) -> ReferralEvent | None:
        # prevent duplicate signup by same referee
        for e in self._events:
            if e.referee_user_id == str(referee_user_id) and e.event_type == "signup":
                return None
        evt = ReferralEvent(
            id=_uuid(),
            code_id=code.id,
            code=code.code,
            referrer_user_id=code.owner_user_id,
            referee_user_id=str(referee_user_id),
            event_type="signup",
            meta=dict(meta or {}),
        )
        self._events.append(evt)
        # increment counter
        code.uses_count = int(code.uses_count or 0) + 1
        return evt

    async def count_signups(self, referrer_user_id: str) -> int:
        return sum(
            1
            for e in self._events
            if e.referrer_user_id == str(referrer_user_id) and e.event_type == "signup"
        )

    async def list_codes(
        self, *, owner_user_id: str | None, active: bool | None, limit: int, offset: int
    ) -> list[ReferralCode]:
        items = list(self._codes_by_user.values())
        if owner_user_id is not None:
            items = [i for i in items if i.owner_user_id == str(owner_user_id)]
        if active is not None:
            items = [i for i in items if bool(i.active) == bool(active)]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[offset : offset + limit]

    async def list_events(
        self, *, referrer_user_id: str | None, limit: int, offset: int
    ) -> list[ReferralEvent]:
        items = [
            e
            for e in self._events
            if (referrer_user_id is None or e.referrer_user_id == str(referrer_user_id))
        ]
        items.sort(key=lambda x: x.occurred_at, reverse=True)
        return items[offset : offset + limit]

    async def generate_unique_code(self, prefix: str = "ref-") -> str:
        for _ in range(10):
            c = (prefix + uuid.uuid4().hex[:12]).lower()
            if c not in self._codes_by_code:
                return c
        return (prefix + uuid.uuid4().hex[:16]).lower()

    async def set_active(self, owner_user_id: str, active: bool) -> ReferralCode | None:
        code = self._codes_by_user.get(str(owner_user_id))
        if code is None and active:
            code = await self.create_personal_code(
                str(owner_user_id), await self.generate_unique_code()
            )
        if not code:
            return None
        code.active = bool(active)
        return code
