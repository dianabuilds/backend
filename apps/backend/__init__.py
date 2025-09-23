from __future__ import annotations

# Convenience re-exports for API routers and DI container accessor
from .app.api_gateway.routers import get_container  # noqa: F401

__all__ = ["get_container"]
