"""
Premium plans API (compat shim).

This module re-exports the public plan helpers from the application layer.
Historically these lived in ``plans_impl.py``; direct usage of that file is
deprecated. Please import from ``app.domains.premium.application.plan_service``
or keep using this module for backwards compatibility.
"""

from app.domains.premium.application.plan_service import (
    build_quota_plans_map,  # noqa: F401
    get_active_plans,  # noqa: F401
    get_effective_plan_slug,  # noqa: F401
    get_plan_by_slug,  # noqa: F401
)

__all__ = [
    "get_active_plans",
    "get_plan_by_slug",
    "build_quota_plans_map",
    "get_effective_plan_slug",
]
