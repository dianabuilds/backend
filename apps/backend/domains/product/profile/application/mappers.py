from __future__ import annotations

from datetime import UTC, datetime, timedelta

from domains.product.profile.domain.entities import Profile
from domains.product.profile.domain.results import (
    ProfileLimitsView,
    ProfileView,
    WalletView,
)


def to_view(profile: Profile, *, cooldown: timedelta) -> ProfileView:
    now = datetime.now(UTC)

    next_username_change_at = (
        profile.last_username_change_at + cooldown
        if profile.last_username_change_at
        else None
    )
    can_change_username = True
    if next_username_change_at and next_username_change_at > now:
        can_change_username = False

    next_email_change_at = (
        profile.last_email_change_at + cooldown
        if profile.last_email_change_at
        else None
    )
    can_change_email = True
    if next_email_change_at and next_email_change_at > now:
        can_change_email = False

    limits = ProfileLimitsView(
        can_change_username=can_change_username,
        next_username_change_at=next_username_change_at,
        can_change_email=can_change_email,
        next_email_change_at=next_email_change_at,
    )

    wallet = WalletView(
        address=profile.wallet_address,
        chain_id=profile.wallet_chain_id,
        verified_at=profile.wallet_verified_at,
    )

    role = profile.role
    if role and role.lower() == "user":
        role = None

    return ProfileView(
        id=profile.id,
        username=profile.username,
        email=profile.email,
        pending_email=profile.pending_email,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        role=role,
        wallet=wallet,
        limits=limits,
    )
