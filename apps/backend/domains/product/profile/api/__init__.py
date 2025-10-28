"""API package for domain product.profile."""

from .admin import make_router as make_admin_router
from .http import make_router
from .public import make_router as make_public_router

__all__ = ["make_router", "make_admin_router", "make_public_router"]
