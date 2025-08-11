import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.config import settings
from app.core.rate_limit import recent_429
from app.db.session import get_db
from app.models.user import User
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
