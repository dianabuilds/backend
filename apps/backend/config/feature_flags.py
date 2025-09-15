from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class FeatureFlags(BaseSettings):
    """Application feature flags."""

    model_config = SettingsConfigDict(env_prefix="FF_", case_sensitive=False)

    profile_enabled: bool = True
    tags_v1_enabled: bool = True
    nodes_v1_enabled: bool = True
    referrals_program: bool = False
    routing_accounts_v2: bool = False
    nodes_legacy_type_routes: bool = True
    quests_v2_enabled: bool = True
    navigation_v2_enabled: bool = True
    ai_v1_enabled: bool = True
    moderation_v1_enabled: bool = True
    premium_enabled: bool = True


feature_flags = FeatureFlags()
