from __future__ import annotations

from datetime import datetime

from domains.product.profile.application.ports import Repo
from domains.product.profile.domain.entities import Profile


class MemoryRepo(Repo):
    def __init__(self) -> None:
        self._profiles: dict[str, Profile] = {}
        self._email_requests: dict[str, tuple[str, str, datetime]] = {}

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

    def get(self, user_id: str) -> Profile | None:  # noqa: A002
        profile = self._profiles.get(id)
        return self._copy(profile) if profile else None

    def update_profile(
        self,
        user_id: str,
        *,
        updates: dict[str, object | None],
        set_username_timestamp: bool,
        now: datetime,
    ) -> Profile:
        profile = self._profiles.get(id)
        if not profile:
            profile = Profile(id=id)
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
        self._profiles[id] = self._copy(profile)
        return self._copy(profile)

    def email_in_use(self, email: str, exclude_user_id: str | None = None) -> bool:
        for uid, profile in self._profiles.items():
            if exclude_user_id and uid == exclude_user_id:
                continue
            if profile.email and profile.email.lower() == email.lower():
                return True
        for uid, (_, pending_email, _) in self._email_requests.items():
            if exclude_user_id and uid == exclude_user_id:
                continue
            if pending_email.lower() == email.lower():
                return True
        return False

    def create_email_change_request(
        self,
        user_id: str,
        *,
        email: str,
        token: str,
        requested_at: datetime,
    ) -> None:
        profile = self._profiles.get(id)
        if not profile:
            profile = Profile(id=id)
        profile.pending_email = email
        profile.email_change_requested_at = requested_at
        self._profiles[id] = self._copy(profile)
        self._email_requests[id] = (token, email, requested_at)

    def confirm_email_change(
        self,
        user_id: str,
        *,
        token: str,
        now: datetime,
    ) -> Profile:
        record = self._email_requests.get(id)
        if not record or record[0] != token:
            raise ValueError("email_change_not_found")
        _, email, _requested_at = record
        profile = self._profiles.get(id)
        if not profile:
            profile = Profile(id=id)
        profile.email = email
        profile.pending_email = None
        profile.email_change_requested_at = None
        profile.last_email_change_at = now
        self._profiles[id] = self._copy(profile)
        self._email_requests.pop(id, None)
        return self._copy(profile)

    def set_wallet(
        self,
        user_id: str,
        *,
        address: str,
        chain_id: str | None,
        signature: str | None,
        verified_at: datetime,
    ) -> Profile:
        profile = self._profiles.get(id)
        if not profile:
            profile = Profile(id=id)
        profile.wallet_address = address
        profile.wallet_chain_id = chain_id
        profile.wallet_verified_at = verified_at
        self._profiles[id] = self._copy(profile)
        return self._copy(profile)

    def clear_wallet(self, user_id: str) -> Profile:
        profile = self._profiles.get(id)
        if not profile:
            profile = Profile(id=id)
        profile.wallet_address = None
        profile.wallet_chain_id = None
        profile.wallet_verified_at = None
        self._profiles[id] = self._copy(profile)
        return self._copy(profile)


__all__ = ["MemoryRepo"]
