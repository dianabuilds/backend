from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import require_role
from app.core.config import settings
from app.models.user import User
from app.core.rate_limit import close_rate_limiter

router = APIRouter(prefix="/admin/ratelimit", tags=["admin"])

_recent_429: list[dict] = []

@router.get('/rules', summary='List rate limit rules')
async def list_rules(current_user: User = Depends(require_role('moderator'))):
    rl = settings.rate_limit
    return {
        'enabled': rl.enabled,
        'rules_login': rl.rules_login,
        'rules_login_json': rl.rules_login_json,
        'rules_signup': rl.rules_signup,
        'rules_evm_nonce': rl.rules_evm_nonce,
        'rules_evm_verify': rl.rules_evm_verify,
        'rules_change_password': rl.rules_change_password,
    }

@router.get('/recent429', summary='Recent 429 events')
async def recent_429(current_user: User = Depends(require_role('moderator'))):
    return {'events': _recent_429[-100:]}

@router.post('/disable', summary='Disable rate limiting (dev only)')
async def disable_rate_limit(current_user: User = Depends(require_role('admin'))):
    if settings.is_production:
        raise HTTPException(status_code=400, detail='not allowed in production')
    settings.rate_limit.enabled = False
    await close_rate_limiter()
    return {'status': 'disabled'}
