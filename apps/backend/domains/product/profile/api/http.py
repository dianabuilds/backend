from __future__ import annotations

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
from domains.product.profile.application.exceptions import ProfileError
from domains.product.profile.application.profile_use_cases import (
    UseCaseResult,
    bind_wallet,
    confirm_email_change,
    get_profile_admin,
    get_profile_me,
    legacy_update_username,
    request_email_change,
    unbind_wallet,
    update_profile,
    upload_avatar,
)
from packages.core.settings_contract import set_etag

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


def _apply_use_case_result(response: Response, result: UseCaseResult) -> dict:
    if result.status_code:
        response.status_code = int(result.status_code)
    if result.headers:
        for key, value in result.headers.items():
            response.headers[key] = value
    if result.etag:
        set_etag(response, result.etag)
    return result.payload


def _raise_profile_error(error: ProfileError) -> None:
    headers = dict(error.headers) if error.headers else None
    raise HTTPException(
        status_code=error.status_code, detail=error.code, headers=headers
    ) from error


def make_router() -> APIRouter:
    router = APIRouter(prefix="/v1/profile")

    @router.get("/me")
    async def fetch_profile_me(
        request: Request,
        response: Response,
        claims=Depends(get_current_user),
        container=Depends(get_container),
    ) -> dict:
        user_id = str(claims.get("sub")) if claims and claims.get("sub") else None
        if not user_id:
            raise HTTPException(status_code=401, detail="unauthenticated") from None
        try:
            result = await get_profile_me(container.profile_service, user_id)
        except ProfileError as error:
            _raise_profile_error(error)
        return _apply_use_case_result(response, result)

    @router.put("/me")
    async def update_profile_me(
        body: ProfileUpdateIn,
        request: Request,
        response: Response,
        claims=Depends(get_current_user),
        container=Depends(get_container),
        if_match: str | None = Header(default=None, alias="If-Match"),
    ) -> dict:
        user_id = str(claims.get("sub")) if claims and claims.get("sub") else None
        if not user_id:
            raise HTTPException(status_code=401, detail="unauthenticated") from None
        subject = _subject_from_claims(claims, user_id)
        try:
            result = await update_profile(
                container.profile_service,
                user_id,
                body.model_dump(exclude_unset=True),
                subject=subject,
                if_match=if_match,
            )
        except ProfileError as error:
            _raise_profile_error(error)
        return _apply_use_case_result(response, result)

    @router.post("/me/avatar")
    async def upload_avatar_me(
        request: Request,
        response: Response,
        file: UploadFile = File(...),
        claims=Depends(get_current_user),
        container=Depends(get_container),
        _csrf: None = Depends(csrf_protect),
    ) -> dict:
        user_id = str(claims.get("sub")) if claims and claims.get("sub") else None
        if not user_id:
            raise HTTPException(status_code=401, detail="unauthenticated") from None
        data = await file.read()
        storage = StorageService(container.media.storage)
        try:
            result = await upload_avatar(
                storage,
                file_name=file.filename or "avatar",
                content=data,
                content_type=file.content_type or "",
                max_size=MAX_AVATAR_SIZE_BYTES,
                allowed_types=ALLOWED_AVATAR_CONTENT_TYPES,
            )
        except ProfileError as error:
            _raise_profile_error(error)
        return _apply_use_case_result(response, result)

    @router.post(
        "/me/email/request-change", dependencies=[Depends(require_idempotency_key)]
    )
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
        subject = _subject_from_claims(claims, user_id)
        try:
            result = await request_email_change(
                container.profile_service,
                user_id,
                payload.email,
                subject=subject,
            )
        except ProfileError as error:
            _raise_profile_error(error)
        return result.payload

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
        subject = _subject_from_claims(claims, user_id)
        try:
            result = await confirm_email_change(
                container.profile_service,
                user_id,
                payload.token,
                subject=subject,
            )
        except ProfileError as error:
            _raise_profile_error(error)
        return _apply_use_case_result(response, result)

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
        subject = _subject_from_claims(claims, user_id)
        try:
            result = await bind_wallet(
                container.profile_service,
                user_id,
                payload.model_dump(exclude_unset=True),
                subject=subject,
            )
        except ProfileError as error:
            _raise_profile_error(error)
        return _apply_use_case_result(response, result)

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
        subject = _subject_from_claims(claims, user_id)
        try:
            result = await unbind_wallet(
                container.profile_service,
                user_id,
                subject=subject,
            )
        except ProfileError as error:
            _raise_profile_error(error)
        return _apply_use_case_result(response, result)

    @router.get("/{user_id}", dependencies=[Depends(require_admin)])
    async def fetch_profile_admin(
        user_id: str,
        request: Request,
        response: Response,
        container=Depends(get_container),
    ) -> dict:
        try:
            result = await get_profile_admin(container.profile_service, user_id)
        except ProfileError as error:
            _raise_profile_error(error)
        return _apply_use_case_result(response, result)

    @router.put("/{user_id}", dependencies=[Depends(require_admin)])
    async def update_profile_admin(
        user_id: str,
        body: ProfileUpdateIn,
        request: Request,
        response: Response,
        container=Depends(get_container),
        if_match: str | None = Header(default=None, alias="If-Match"),
    ) -> dict:
        subject = {"user_id": user_id}
        try:
            result = await update_profile(
                container.profile_service,
                user_id,
                body.model_dump(exclude_unset=True),
                subject=subject,
                if_match=if_match,
            )
        except ProfileError as error:
            _raise_profile_error(error)
        return _apply_use_case_result(response, result)

    @router.put("/{user_id}/username")
    async def legacy_update_username_route(
        user_id: str,
        body: dict,
        request: Request,
        response: Response,
        container=Depends(get_container),
        claims=Depends(get_current_user),
        _csrf: None = Depends(csrf_protect),
    ) -> dict:
        username = body.get("username")
        if not isinstance(username, str):
            raise HTTPException(status_code=400, detail="username_required") from None
        sub = str(claims.get("sub")) if claims and claims.get("sub") else None
        role = str(claims.get("role") or "").lower() if claims else ""
        if sub != user_id and role != "admin":
            raise HTTPException(status_code=403, detail="forbidden") from None
        subject = _subject_from_claims(claims, user_id)
        try:
            result = await legacy_update_username(
                container.profile_service,
                user_id,
                username,
                subject=subject,
            )
        except ProfileError as error:
            _raise_profile_error(error)
        return _apply_use_case_result(response, result)

    return router


__all__ = ["make_router"]
