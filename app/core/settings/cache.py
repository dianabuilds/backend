from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CacheSettings(BaseSettings):
    redis_url: str | None = Field(default=None, alias="REDIS_URL")
    nav_cache_ttl: int = Field(300, alias="NAV_CACHE_TTL")
    compass_cache_ttl: int = Field(120, alias="COMPASS_CACHE_TTL")
    enable_nav_cache: bool = Field(True, alias="CACHE_ENABLE_NAV_CACHE")
    enable_compass_cache: bool = Field(True, alias="CACHE_ENABLE_COMPASS_CACHE")
    key_version: str = Field("v1", alias="CACHE_KEY_VERSION")

    model_config = SettingsConfigDict(extra="ignore")
