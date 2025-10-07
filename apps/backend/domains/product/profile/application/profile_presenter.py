from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from http import HTTPStatus
from typing import Any, TypedDict

from domains.product.profile.domain.results import (
    EmailChangeRequest,
    ProfileLimitsView,
    ProfileView,
    WalletView,
)
from packages.core.settings_contract import compute_etag


class WalletPayload(TypedDict, total=False):
    address: str | None
    chain_id: str | None
    verified_at: str | None


class ProfileLimitsPayload(TypedDict, total=False):
    can_change_username: bool
    next_username_change_at: str | None
    can_change_email: bool
    next_email_change_at: str | None


class ProfilePayload(TypedDict, total=False):
    id: str
    username: str | None
    email: str | None
    pending_email: str | None
    bio: str | None
    avatar_url: str | None
    role: str | None
    wallet: WalletPayload
    limits: ProfileLimitsPayload


class ProfileEnvelope(TypedDict):
    profile: ProfilePayload


class EmailChangeResponse(TypedDict, total=False):
    status: str
    pending_email: str | None
    token: str | None


class AvatarFilePayload(TypedDict):
    url: str


class AvatarResponse(TypedDict):
    success: int
    url: str
    file: AvatarFilePayload


@dataclass(slots=True)
class ResponseMeta:
    status_code: int = HTTPStatus.OK
    etag: str | None = None
    headers: Mapping[str, str] | None = None


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def serialize_wallet(wallet: WalletView) -> WalletPayload:
    return {
        "address": wallet.address,
        "chain_id": wallet.chain_id,
        "verified_at": _iso(wallet.verified_at),
    }


def serialize_limits(limits: ProfileLimitsView) -> ProfileLimitsPayload:
    return {
        "can_change_username": limits.can_change_username,
        "next_username_change_at": _iso(limits.next_username_change_at),
        "can_change_email": limits.can_change_email,
        "next_email_change_at": _iso(limits.next_email_change_at),
    }


def profile_to_dict(view: ProfileView) -> ProfilePayload:
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


def profile_etag(payload: ProfileView | Mapping[str, Any]) -> str:
    data = (
        profile_to_dict(payload) if isinstance(payload, ProfileView) else dict(payload)
    )
    return compute_etag(data)


def build_profile_response(view: ProfileView) -> ProfilePayload:
    return profile_to_dict(view)


def build_profile_payload(view: ProfileView) -> ProfileEnvelope:
    return {"profile": profile_to_dict(view)}


def build_email_change_response(result: EmailChangeRequest) -> EmailChangeResponse:
    return {
        "status": result.status,
        "pending_email": result.pending_email,
        "token": result.token,
    }


def build_avatar_response(url: str) -> AvatarResponse:
    return {
        "success": 1,
        "url": url,
        "file": {"url": url},
    }


def build_profile_result(
    view: ProfileView,
    *,
    status: HTTPStatus = HTTPStatus.OK,
) -> tuple[ProfilePayload, ResponseMeta]:
    payload = build_profile_response(view)
    meta = ResponseMeta(status_code=int(status), etag=profile_etag(payload))
    return payload, meta


def build_profile_settings_result(
    view: ProfileView,
) -> tuple[ProfileEnvelope, ResponseMeta]:
    payload = build_profile_payload(view)
    meta = ResponseMeta(etag=profile_etag(payload))
    return payload, meta


def build_email_change_result(
    result: EmailChangeRequest,
    *,
    status: HTTPStatus = HTTPStatus.OK,
) -> tuple[EmailChangeResponse, ResponseMeta]:
    payload = build_email_change_response(result)
    meta = ResponseMeta(status_code=int(status))
    return payload, meta


def build_avatar_result(url: str) -> tuple[AvatarResponse, ResponseMeta]:
    payload = build_avatar_response(url)
    meta = ResponseMeta(status_code=int(HTTPStatus.OK))
    return payload, meta


__all__ = [
    "AvatarFilePayload",
    "AvatarResponse",
    "EmailChangeResponse",
    "ProfileEnvelope",
    "ProfileLimitsPayload",
    "ProfilePayload",
    "ResponseMeta",
    "build_avatar_response",
    "build_avatar_result",
    "build_email_change_response",
    "build_email_change_result",
    "build_profile_payload",
    "build_profile_response",
    "build_profile_result",
    "build_profile_settings_result",
    "profile_etag",
    "profile_to_dict",
    "serialize_limits",
    "serialize_wallet",
]
