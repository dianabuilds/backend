"""
Domains.Premium: Public API re-export.

from app.domains.premium.api_public import router
"""
from app.api.premium_limits import router

__all__ = ["router"]
