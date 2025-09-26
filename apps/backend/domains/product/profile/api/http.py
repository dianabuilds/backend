from __future__ import annotations

import io

from fastapi import (
    APIRouter,
    Depends,
    File,
    Header,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from pydantic import BaseModel, Field

from app.api_gateway.idempotency import require_idempotency_key
from apps.backend import get_container
from domains.platform.iam.security import csrf_protect, get_current_user, require_admin
from domains.platform.media.application.storage_service import StorageService
from packages.core.settings_contract import assert_if_match, compute_etag, set_etag

ALLOWED_AVATAR_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_AVATAR_SIZE_BYTES = 5 * 1024 * 1024


class ProfileUpdateIn(BaseModel):
    username: str | None = Field(default=None)
    bio: str | None = Field(default=None)
    avatar_url: str | None = Field(default=None)


class WalletBindIn(BaseModel):
    address: str
    chain_id: str | None = None
    signature: str | None = None


class EmailChangeIn(BaseModel):
    email: str


class EmailConfirmIn(BaseModel):
    token: str


def _subject_from_claims(claims: dict | None, fallback_user_id: str) -> dict:
    subject: dict[str, str] = {}
    if claims:
        if claims.get("sub"):
            subject["user_id"] = str(claims.get("sub"))
        if claims.get("role"):
            subject["role"] = str(claims.get("role"))
    if "user_id" not in subject:
        subject["user_id"] = fallback_user_id
    return subject


def _profile_etag(payload: dict) -> str:
    return compute_etag(payload)


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/profile")

    async def _admin_get_profile(
        user_id: str,
        req: Request,
        response: Response,
        container=Depends(get_container),
    ) -> dict:
        svc = container.profile_service
        try:
            profile = await svc.get_profile(user_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="profile_not_found") from None
        set_etag(response, _profile_etag(profile))
        return profile

    @router.get("/me")
    async def get_profile_me(
        req: Request,
        response: Response,
        claims=Depends(get_current_user),
        container=Depends(get_container),
    ) -> dict:
        user_id = str(claims.get("sub")) if claims and claims.get("sub") else None
        if not user_id:
            raise HTTPException(status_code=401, detail="unauthenticated") from None
        svc = container.profile_service
        try:
            profile = await svc.get_profile(user_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="profile_not_found") from None
        set_etag(response, _profile_etag(profile))
        return profile

    async def _update_profile(
        target_user_id: str,
        body: ProfileUpdateIn,
        if_match: str | None,
        req: Request,
        response: Response,
        claims: dict | None,
        container,
    ) -> dict:
        svc = container.profile_service
        try:
            current = await svc.get_profile(target_user_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="profile_not_found") from None
        current_etag = _profile_etag(current)
        assert_if_match(if_match, current_etag)
        subject = _subject_from_claims(claims, target_user_id)
        payload = body.model_dump(exclude_unset=True)
        try:
            updated = await svc.update_profile(target_user_id, payload, subject=subject)
        except PermissionError:
            raise HTTPException(status_code=403, detail="forbidden") from None
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        set_etag(response, _profile_etag(updated))
        return updated

    @router.put("/me")
    async def update_profile_me(
        body: ProfileUpdateIn,
        request: Request,
        response: Response,
        if_match: str | None = Header(default=None, alias="If-Match"),
        claims=Depends(get_current_user),
        container=Depends(get_container),
    ) -> dict:
        user_id = str(claims.get("sub")) if claims and claims.get("sub") else None
        if not user_id:
            raise HTTPException(status_code=401, detail="unauthenticated") from None
        return await _update_profile(user_id, body, if_match, request, response, claims, container)

    @router.post("/me/avatar")
    async def upload_avatar_me(
        request: Request,
        file: UploadFile = File(...),
        claims=Depends(get_current_user),
        container=Depends(get_container),
        _csrf: None = Depends(csrf_protect),
    ) -> dict:
        user_id = str(claims.get("sub")) if claims and claims.get("sub") else None
        if not user_id:
            raise HTTPException(status_code=401, detail="unauthenticated") from None
        if not file.content_type or file.content_type not in ALLOWED_AVATAR_CONTENT_TYPES:
            raise HTTPException(status_code=415, detail="unsupported_media_type") from None
        data = await file.read()
        if len(data) > MAX_AVATAR_SIZE_BYTES:
            raise HTTPException(status_code=413, detail="file_too_large") from None
        storage = StorageService(container.media.storage)
        filename = file.filename or "avatar"
        url = storage.save_file(io.BytesIO(data), filename, file.content_type)
        return {"success": 1, "url": url, "file": {"url": url}}

    async def _admin_update_profile(
        user_id: str,
        body: ProfileUpdateIn,
        request: Request,
        response: Response,
        if_match: str | None = Header(default=None, alias="If-Match"),
        container=Depends(get_container),
    ) -> dict:
        return await _update_profile(user_id, body, if_match, request, response, None, container)

    async def _legacy_update_username(
        user_id: str,
        body: dict,
        request: Request,
        response: Response,
        container=Depends(get_container),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ) -> dict:
        sub = str(claims.get("sub")) if claims else None
        role = str(claims.get("role") or "").lower()
        if sub != user_id and role != "admin":
            raise HTTPException(status_code=403, detail="forbidden") from None
        username = body.get("username")
        if not isinstance(username, str) or not username.strip():
            raise HTTPException(status_code=400, detail="username_required") from None
        svc = container.profile_service
        subject = _subject_from_claims(claims, user_id)
        try:
            updated = await svc.update_profile(
                user_id,
                {"username": username},
                subject=subject,
            )
        except PermissionError:
            raise HTTPException(status_code=403, detail="forbidden") from None
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        set_etag(response, _profile_etag(updated))
        return updated

    router.add_api_route(
        "/{user_id}",
        _admin_get_profile,
        methods=["GET"],
        dependencies=[Depends(require_admin)],
    )
    router.add_api_route(
        "/{user_id}",
        _admin_update_profile,
        methods=["PUT"],
        dependencies=[Depends(require_admin)],
    )
    router.add_api_route(
        "/{user_id}/username",
        _legacy_update_username,
        methods=["PUT"],
    )

    @router.post("/me/email/request-change", dependencies=[Depends(require_idempotency_key)])
    async def request_email_change_me(
        payload: EmailChangeIn,
        request: Request,
        claims=Depends(get_current_user),
        container=Depends(get_container),
        _csrf: None = Depends(csrf_protect),
    ) -> dict:
        user_id = str(claims.get("sub")) if claims and claims.get("sub") else None
        if not user_id:
            raise HTTPException(status_code=401, detail="unauthenticated") from None
        svc = container.profile_service
        subject = _subject_from_claims(claims, user_id)
        try:
            result = await svc.request_email_change(user_id, payload.email, subject=subject)
        except PermissionError:
            raise HTTPException(status_code=403, detail="forbidden") from None
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return result

    @router.post("/me/email/confirm")
    async def confirm_email_change_me(
        payload: EmailConfirmIn,
        request: Request,
        response: Response,
        claims=Depends(get_current_user),
        container=Depends(get_container),
        _csrf: None = Depends(csrf_protect),
    ) -> dict:
        user_id = str(claims.get("sub")) if claims and claims.get("sub") else None
        if not user_id:
            raise HTTPException(status_code=401, detail="unauthenticated") from None
        svc = container.profile_service
        subject = _subject_from_claims(claims, user_id)
        try:
            updated = await svc.confirm_email_change(user_id, payload.token, subject=subject)
        except PermissionError:
            raise HTTPException(status_code=403, detail="forbidden") from None
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        set_etag(response, _profile_etag(updated))
        return updated

    @router.post("/me/wallet")
    async def bind_wallet_me(
        payload: WalletBindIn,
        request: Request,
        response: Response,
        claims=Depends(get_current_user),
        container=Depends(get_container),
        _csrf: None = Depends(csrf_protect),
    ) -> dict:
        user_id = str(claims.get("sub")) if claims and claims.get("sub") else None
        if not user_id:
            raise HTTPException(status_code=401, detail="unauthenticated") from None
        svc = container.profile_service
        subject = _subject_from_claims(claims, user_id)
        try:
            updated = await svc.set_wallet(
                user_id,
                address=payload.address,
                chain_id=payload.chain_id,
                signature=payload.signature,
                subject=subject,
            )
        except PermissionError:
            raise HTTPException(status_code=403, detail="forbidden") from None
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        set_etag(response, _profile_etag(updated))
        return updated

    @router.delete("/me/wallet")
    async def unbind_wallet_me(
        request: Request,
        response: Response,
        claims=Depends(get_current_user),
        container=Depends(get_container),
        _csrf: None = Depends(csrf_protect),
    ) -> dict:
        user_id = str(claims.get("sub")) if claims and claims.get("sub") else None
        if not user_id:
            raise HTTPException(status_code=401, detail="unauthenticated") from None
        svc = container.profile_service
        subject = _subject_from_claims(claims, user_id)
        try:
            updated = await svc.clear_wallet(user_id, subject)
        except PermissionError:
            raise HTTPException(status_code=403, detail="forbidden") from None
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        set_etag(response, _profile_etag(updated))
        return updated

    return router
