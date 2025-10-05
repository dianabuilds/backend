from __future__ import annotations

from datetime import datetime
from typing import Any

from domains.product.profile.domain.results import (
    EmailChangeRequest,
    ProfileLimitsView,
    ProfileView,
    WalletView,
)
from packages.core.settings_contract import compute_etag


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def serialize_wallet(wallet: WalletView) -> dict[str, Any]:
    return {
        "address": wallet.address,
        "chain_id": wallet.chain_id,
        "verified_at": _iso(wallet.verified_at),
    }


def serialize_limits(limits: ProfileLimitsView) -> dict[str, Any]:
    return {
        "can_change_username": limits.can_change_username,
        "next_username_change_at": _iso(limits.next_username_change_at),
        "can_change_email": limits.can_change_email,
        "next_email_change_at": _iso(limits.next_email_change_at),
    }


def profile_to_dict(view: ProfileView) -> dict[str, Any]:
    return {
        "id": view.id,
        "username": view.username,
        "email": view.email,
        "pending_email": view.pending_email,
        "bio": view.bio,
        "avatar_url": view.avatar_url,
        "role": view.role,
        "wallet": serialize_wallet(view.wallet),
        "limits": serialize_limits(view.limits),
    }


def profile_etag(payload: ProfileView | dict[str, Any]) -> str:
    data = profile_to_dict(payload) if isinstance(payload, ProfileView) else payload
    return compute_etag(data)


def build_profile_response(view: ProfileView) -> dict[str, Any]:
    return profile_to_dict(view)


def build_profile_payload(view: ProfileView) -> dict[str, Any]:
    return {"profile": profile_to_dict(view)}


def build_email_change_response(result: EmailChangeRequest) -> dict[str, Any]:
    return {
        "status": result.status,
        "pending_email": result.pending_email,
        "token": result.token,
    }


def build_avatar_response(url: str) -> dict[str, Any]:
    return {
        "success": 1,
        "url": url,
        "file": {"url": url},
    }


__all__ = [
    "build_avatar_response",
    "build_email_change_response",
    "build_profile_payload",
    "build_profile_response",
    "profile_etag",
    "profile_to_dict",
    "serialize_limits",
    "serialize_wallet",
]
