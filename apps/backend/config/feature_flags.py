from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class FeatureFlags(BaseSettings):
    """Application feature flags."""

    model_config = SettingsConfigDict(env_prefix="FF_", case_sensitive=False)

    profile_enabled: bool = True
    referrals_program: bool = False
    routing_accounts_v2: bool = False
    # Allow legacy admin routes under /admin/accounts/{account_id}/nodes/types/*
    # When false, only ID-based routes are registered.
    nodes_legacy_type_routes: bool = True


feature_flags = FeatureFlags()
