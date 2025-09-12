from __future__ import annotations

from pydantic import BaseModel


class FeatureFlagsOut(BaseModel):
    profile_enabled: bool
    referrals_program: bool | None = None
    routing_accounts_v2: bool | None = None
    nodes_legacy_type_routes: bool | None = None

__all__ = ["FeatureFlagsOut"]

