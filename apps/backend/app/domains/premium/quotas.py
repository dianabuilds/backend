"""
Premium quotas API (compat shim).

This module re-exports quota helpers from the application layer.
Legacy ``quotas_impl.py`` is deprecated; import from
``app.domains.premium.application.user_quota_service`` instead or keep using
this shim during migration.
"""

from app.domains.premium.application.user_quota_service import (  # noqa: F401
    check_and_consume_quota,
    get_quota_status,
)

__all__ = ["check_and_consume_quota", "get_quota_status"]
