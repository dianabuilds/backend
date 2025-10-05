from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from domains.product.profile.application.mappers import to_view
from domains.product.profile.application.ports import IamClient, Outbox, Repo
from domains.product.profile.domain.entities import Profile
from domains.product.profile.domain.results import EmailChangeRequest, ProfileView
from packages.core import Flags

COOLDOWN_DAYS = 14


class Service:
    def __init__(
        self,
        repo: Repo,
        outbox: Outbox,
        iam: IamClient,
        flags: Flags,
        *,
        cooldown: timedelta | None = None,
    ) -> None:
        self.repo, self.outbox, self.iam, self.flags = repo, outbox, iam, flags
        self.cooldown = cooldown or timedelta(days=COOLDOWN_DAYS)

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _to_view(self, profile: Profile) -> ProfileView:
        return to_view(profile, cooldown=self.cooldown)

    async def get_profile(self, user_id: str) -> ProfileView:
        profile = await self.repo.get(user_id)
        if not profile:
            raise ValueError("profile_not_found")
        return self._to_view(profile)

    async def update_profile(
        self,
        user_id: str,
        payload: dict[str, Any],
        subject: dict,
    ) -> ProfileView:
        if not self.iam.allow(subject, "profile.update", {"user_id": user_id}):
            raise PermissionError("denied")

        current = await self.repo.get(user_id)
        if not current:
            raise ValueError("profile_not_found")

        updates: dict[str, Any] = {}
        username_changed = False

        if "username" in payload:
            new_username_raw = payload.get("username")
            new_username = None
            if isinstance(new_username_raw, str):
                trimmed = new_username_raw.strip()
                new_username = trimmed or None
            elif new_username_raw is None:
                new_username = None
            else:
                raise ValueError("invalid_username")

            if new_username is None:
                raise ValueError("username_required")

            if new_username != current.username:
                current.rename(new_username)
                if current.last_username_change_at:
                    next_allowed = current.last_username_change_at + self.cooldown
                    if next_allowed > self._now():
                        raise ValueError("username_rate_limited")
                updates["username"] = new_username
                username_changed = True

        if "bio" in payload:
            bio_val = payload.get("bio")
            if bio_val is not None and not isinstance(bio_val, str):
                raise ValueError("invalid_bio")
            if isinstance(bio_val, str) and len(bio_val) > 1024:
                raise ValueError("bio_too_long")
            updates["bio"] = bio_val

        if "avatar_url" in payload:
            avatar_val = payload.get("avatar_url")
            if avatar_val is not None and not isinstance(avatar_val, str):
                raise ValueError("invalid_avatar")
            if isinstance(avatar_val, str) and len(avatar_val) > 2048:
                raise ValueError("avatar_too_long")
            updates["avatar_url"] = avatar_val

        if not updates:
            return self._to_view(current)

        updated = await self.repo.update_profile(
            user_id,
            updates=updates,
            set_username_timestamp=username_changed,
            now=self._now(),
        )

        event_payload = {"id": updated.id, "username": updated.username}
        if "bio" in updates:
            event_payload["bio"] = updated.bio
        self.outbox.publish(
            "profile.updated.v1",
            event_payload,
            key=updated.id,
        )
        return self._to_view(updated)

    async def request_email_change(
        self,
        user_id: str,
        new_email: str,
        subject: dict,
    ) -> EmailChangeRequest:
        if not self.iam.allow(subject, "profile.update", {"user_id": user_id}):
            raise PermissionError("denied")

        if not isinstance(new_email, str) or not new_email.strip():
            raise ValueError("invalid_email")
        normalized_email = new_email.strip().lower()
        if "@" not in normalized_email or "." not in normalized_email:
            raise ValueError("invalid_email")

        current = await self.repo.get(user_id)
        if not current:
            raise ValueError("profile_not_found")

        if current.last_email_change_at:
            next_allowed = current.last_email_change_at + self.cooldown
            if next_allowed > self._now():
                raise ValueError("email_rate_limited")

        if current.email and current.email.lower() == normalized_email:
            raise ValueError("email_same")

        if await self.repo.email_in_use(normalized_email, exclude_user_id=user_id):
            raise ValueError("email_taken")

        token = uuid4().hex
        now = self._now()
        await self.repo.create_email_change_request(
            user_id,
            email=normalized_email,
            token=token,
            requested_at=now,
        )

        self.outbox.publish(
            "profile.email.change.requested.v1",
            {
                "id": user_id,
                "new_email": normalized_email,
            },
            key=user_id,
        )
        return EmailChangeRequest(
            status="pending", pending_email=normalized_email, token=token
        )

    async def confirm_email_change(
        self,
        user_id: str,
        token: str,
        subject: dict,
    ) -> ProfileView:
        if not self.iam.allow(subject, "profile.update", {"user_id": user_id}):
            raise PermissionError("denied")
        if not isinstance(token, str) or not token.strip():
            raise ValueError("token_required")

        updated = await self.repo.confirm_email_change(
            user_id,
            token=token.strip(),
            now=self._now(),
        )

        self.outbox.publish(
            "profile.email.updated.v1",
            {
                "id": updated.id,
                "email": updated.email,
            },
            key=updated.id,
        )
        return self._to_view(updated)

    async def set_wallet(
        self,
        user_id: str,
        *,
        address: str,
        chain_id: str | None,
        signature: str | None,
        subject: dict,
    ) -> ProfileView:
        if not self.iam.allow(subject, "profile.update", {"user_id": user_id}):
            raise PermissionError("denied")
        if not isinstance(address, str) or not address:
            raise ValueError("wallet_required")
        updated = await self.repo.set_wallet(
            user_id,
            address=address,
            chain_id=chain_id,
            signature=signature,
            verified_at=self._now(),
        )
        self.outbox.publish(
            "profile.wallet.updated.v1",
            {
                "id": updated.id,
                "wallet_address": updated.wallet_address,
                "wallet_chain_id": updated.wallet_chain_id,
            },
            key=updated.id,
        )
        return self._to_view(updated)

    async def clear_wallet(self, user_id: str, subject: dict) -> ProfileView:
        if not self.iam.allow(subject, "profile.update", {"user_id": user_id}):
            raise PermissionError("denied")
        updated = await self.repo.clear_wallet(user_id)
        self.outbox.publish(
            "profile.wallet.cleared.v1",
            {"id": updated.id},
            key=updated.id,
        )
        return self._to_view(updated)
