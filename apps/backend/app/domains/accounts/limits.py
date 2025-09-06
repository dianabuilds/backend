from __future__ import annotations

from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.preview import PreviewContext
from app.domains.accounts.infrastructure.dao import AccountDAO
from app.domains.quota.application.quota_service import QuotaService
from app.schemas.accounts import AccountSettings

_ws_quota_service: QuotaService | None = None


def _get_qs() -> QuotaService:
    global _ws_quota_service
    if _ws_quota_service is None:
        _ws_quota_service = QuotaService()
    return _ws_quota_service


async def consume_account_limit(
    db: AsyncSession,
    user_id: Any,
    account_id: Any,
    key: str,
    *,
    amount: int = 1,
    scope: str = "day",
    degrade: bool = False,
    preview: PreviewContext | None = None,
    log: dict[str, Any] | None = None,
) -> bool:
    ws = await AccountDAO.get(db, account_id)
    if ws is None:
        if log is not None:
            log[key] = {"value": 0, "source": "global"}
        return True
    settings = AccountSettings.model_validate(ws.settings_json)
    limit = settings.limits.get(key)
    source = "account"
    if not limit or int(limit) <= 0:
        try:
            from app.domains.premium.quotas import get_quota_status

            status = await get_quota_status(
                db,
                user_id,
                quota_key=key,
                scope=scope,
                preview=preview,
            )
            limit = status.get("limit")
            source = "global"
        except Exception:
            limit = None
    if log is not None:
        log[key] = {"value": int(limit) if limit else 0, "source": source}
    if not limit or int(limit) <= 0:
        return True
    qs = _get_qs()
    try:
        await qs.consume(
            user_id=str(user_id),
            account_id=str(account_id),
            key=key,
            limit=int(limit),
            amount=amount,
            scope=scope,
            preview=preview,
        )
        return True
    except HTTPException:
        if degrade:
            return False
        raise


def account_limit(
    key: str,
    *,
    scope: str = "day",
    amount: int = 1,
    degrade: bool = False,
) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    """Decorator enforcing account limits."""

    def decorator(func: Callable[..., Awaitable[Any]]):
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            db: AsyncSession | None = kwargs.get("db")
            if db is None and args:
                # try to fetch from repository in self
                self_obj = args[0]
                repo = getattr(self_obj, "_repo", None)
                db = getattr(repo, "_db", None)
            account_id = kwargs.get("account_id")
            user_id = kwargs.get("user_id") or kwargs.get("created_by") or kwargs.get("user")
            uid = getattr(user_id, "id", None)
            if uid is not None:
                user_id = uid
            preview = kwargs.get("preview")
            if db and user_id and account_id:
                allowed = await consume_account_limit(
                    db,
                    user_id,
                    account_id,
                    key,
                    amount=amount,
                    scope=scope,
                    degrade=degrade,
                    preview=preview,
                )
                if not allowed and degrade:
                    return {}
            return await func(*args, **kwargs)

        return wrapper

    return decorator
