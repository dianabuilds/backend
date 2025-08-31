"""
Domains.Premium: Quotas re-export.

from app.domains.premium.quotas import check_and_consume_quota, get_quota_status
"""

from .quotas_impl import check_and_consume_quota, get_quota_status  # noqa: F401

__all__ = ["check_and_consume_quota", "get_quota_status"]
