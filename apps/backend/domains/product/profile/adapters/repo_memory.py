from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import datetime

from domains.product.profile.application.ports import Repo
from domains.product.profile.domain.entities import Profile

_DEFAULT_PROFILE_SEED: tuple[tuple[str, dict[str, object | None]], ...] = (
    (
        "00000000-0000-0000-0000-000000000001",
        {"username": "demo-user", "role": "user"},
    ),
    (
        "00000000-0000-0000-0000-000000000002",
        {"username": "demo-user-2", "role": "user"},
    ),
    (
        "00000000-0000-0000-0000-000000000099",
        {"username": "admin-99", "role": "admin"},
    ),
    (
        str(uuid.uuid5(uuid.NAMESPACE_DNS, "user:author-1")),
        {"username": "author-1", "role": "user"},
    ),
    (
        str(uuid.uuid5(uuid.NAMESPACE_DNS, "user:moderation-author")),
        {"username": "moderation-author", "role": "user"},
    ),
    (
        str(uuid.uuid5(uuid.NAMESPACE_DNS, "user:engagement-author")),
        {"username": "engagement-author", "role": "user"},
    ),
)


def build_default_seed() -> dict[str, Profile]:
    seed: dict[str, Profile] = {}
    for user_id, attrs in _DEFAULT_PROFILE_SEED:
        seed[user_id] = Profile(id=user_id, **attrs)
    return seed


class MemoryRepo(Repo):
    def __init__(self, seed: Mapping[str, Profile] | None = None) -> None:
        self._profiles: dict[str, Profile] = {}
        self._email_requests: dict[str, tuple[str, str, datetime]] = {}
        initial = dict(seed) if seed is not None else build_default_seed()
        for user_id, profile in initial.items():
            self._profiles[user_id] = self._copy(profile)

    def _copy(self, profile: Profile) -> Profile:
        return Profile(
            id=profile.id,
            username=profile.username,
            email=profile.email,
            bio=profile.bio,
            avatar_url=profile.avatar_url,
            role=profile.role,
            wallet_address=profile.wallet_address,
            wallet_chain_id=profile.wallet_chain_id,
            wallet_verified_at=profile.wallet_verified_at,
            pending_email=profile.pending_email,
            email_change_requested_at=profile.email_change_requested_at,
            last_username_change_at=profile.last_username_change_at,
            last_email_change_at=profile.last_email_change_at,
        )

    async def get(self, user_id: str) -> Profile | None:  # noqa: A002
        profile = self._profiles.get(user_id)
        return self._copy(profile) if profile else None

    async def update_profile(
        self,
        user_id: str,
        *,
        updates: dict[str, object | None],
        set_username_timestamp: bool,
        now: datetime,
    ) -> Profile:
        profile = self._profiles.get(user_id)
        if not profile:
            profile = Profile(id=user_id)
        if "username" in updates:
            profile.username = updates["username"]  # type: ignore[assignment]
            if set_username_timestamp:
                profile.last_username_change_at = now
        elif set_username_timestamp:
            profile.last_username_change_at = now
        if "bio" in updates:
            profile.bio = updates["bio"]  # type: ignore[assignment]
        if "avatar_url" in updates:
            profile.avatar_url = updates["avatar_url"]  # type: ignore[assignment]
        self._profiles[user_id] = self._copy(profile)
        return self._copy(profile)

    async def email_in_use(
        self, email: str, exclude_user_id: str | None = None
    ) -> bool:
        lowered = email.lower()
        for uid, profile in self._profiles.items():
            if exclude_user_id and uid == exclude_user_id:
                continue
            if profile.email and profile.email.lower() == lowered:
                return True
        for uid, (_, pending_email, _) in self._email_requests.items():
            if exclude_user_id and uid == exclude_user_id:
                continue
            if pending_email.lower() == lowered:
                return True
        return False

    async def create_email_change_request(
        self,
        user_id: str,
        *,
        email: str,
        token: str,
        requested_at: datetime,
    ) -> None:
        profile = self._profiles.get(user_id)
        if not profile:
            profile = Profile(id=user_id)
        profile.pending_email = email
        profile.email_change_requested_at = requested_at
        self._profiles[user_id] = self._copy(profile)
        self._email_requests[user_id] = (token, email, requested_at)

    async def confirm_email_change(
        self,
        user_id: str,
        *,
        token: str,
        now: datetime,
    ) -> Profile:
        record = self._email_requests.get(user_id)
        if not record or record[0] != token:
            raise ValueError("email_change_not_found")
        _, email, _requested_at = record
        profile = self._profiles.get(user_id)
        if not profile:
            profile = Profile(id=user_id)
        profile.email = email
        profile.pending_email = None
        profile.email_change_requested_at = None
        profile.last_email_change_at = now
        self._profiles[user_id] = self._copy(profile)
        self._email_requests.pop(user_id, None)
        return self._copy(profile)

    async def set_wallet(
        self,
        user_id: str,
        *,
        address: str,
        chain_id: str | None,
        signature: str | None,
        verified_at: datetime,
    ) -> Profile:
        profile = self._profiles.get(user_id)
        if not profile:
            profile = Profile(id=user_id)
        profile.wallet_address = address
        profile.wallet_chain_id = chain_id
        profile.wallet_verified_at = verified_at
        self._profiles[user_id] = self._copy(profile)
        return self._copy(profile)

    async def clear_wallet(self, user_id: str) -> Profile:
        profile = self._profiles.get(user_id)
        if not profile:
            profile = Profile(id=user_id)
        profile.wallet_address = None
        profile.wallet_chain_id = None
        profile.wallet_verified_at = None
        self._profiles[user_id] = self._copy(profile)
        return self._copy(profile)


__all__ = ["MemoryRepo", "build_default_seed"]
