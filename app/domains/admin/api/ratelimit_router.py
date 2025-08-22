import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.config import settings
from app.core.rate_limit import recent_429, _parse_rule  # type: ignore
from app.db.session import get_db
from app.domains.users.infrastructure.models.user import User
from app.security import ADMIN_AUTH_RESPONSES, require_admin_role

admin_required = require_admin_role()
admin_only = require_admin_role({"admin"})

router = APIRouter(
    prefix="/admin/ratelimit",
    tags=["admin"],
    dependencies=[Depends(admin_required)],
    responses=ADMIN_AUTH_RESPONSES,
)
logger = logging.getLogger(__name__)


_ALLOWED_KEYS = {
    "login": "rules_login",
    "login_json": "rules_login_json",
    "signup": "rules_signup",
    "evm_nonce": "rules_evm_nonce",
    "evm_verify": "rules_evm_verify",
    "change_password": "rules_change_password",
}


@router.get("/rules", summary="List rate limit rules")
async def list_rules(current_user: User = Depends(admin_required)):
    return {
        "enabled": settings.rate_limit.enabled,
        "rules": {
            "login": settings.rate_limit.rules_login,
            "login_json": settings.rate_limit.rules_login_json,
            "signup": settings.rate_limit.rules_signup,
            "evm_nonce": settings.rate_limit.rules_evm_nonce,
            "evm_verify": settings.rate_limit.rules_evm_verify,
            "change_password": settings.rate_limit.rules_change_password,
        },
    }


class RuleUpdatePayload(BaseModel):
    key: str
    rule: str


@router.patch("/rules", summary="Update single rate limit rule")
async def update_rule(payload: RuleUpdatePayload, current_user: User = Depends(admin_only)):
    attr = _ALLOWED_KEYS.get(payload.key)
    if not attr:
        raise HTTPException(status_code=400, detail="Unknown rule key")
    try:
        _parse_rule(payload.rule)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid rule format, expected like '5/min', '10/sec', '3/hour'")
    setattr(settings.rate_limit, attr, payload.rule)
    return {
        "ok": True,
        "rules": {
            "login": settings.rate_limit.rules_login,
            "login_json": settings.rate_limit.rules_login_json,
            "signup": settings.rate_limit.rules_signup,
            "evm_nonce": settings.rate_limit.rules_evm_nonce,
            "evm_verify": settings.rate_limit.rules_evm_verify,
            "change_password": settings.rate_limit.rules_change_password,
        },
    }


@router.get("/recent429", summary="Recent rate limit hits")
async def recent_hits(current_user: User = Depends(admin_required)):
    return list(recent_429)


class RateLimitDisablePayload(BaseModel):
    disabled: bool = True


@router.post("/disable", summary="Toggle rate limiter")
async def disable_rate_limit(
    payload: RateLimitDisablePayload,
    current_user: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    if settings.is_production:
        raise HTTPException(status_code=403, detail="Not allowed in production")
    settings.rate_limit.enabled = not payload.disabled
    logger.info(
        "admin_action",
        extra={
            "action": "ratelimit_disable",
            "actor_id": str(current_user.id),
            "disabled": payload.disabled,
            "ts": datetime.utcnow().isoformat(),
        },
    )
    return {"enabled": settings.rate_limit.enabled}
