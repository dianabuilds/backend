from pydantic_settings import BaseSettings, SettingsConfigDict

class CacheSettings(BaseSettings):
    redis_url: str | None = None
    nav_cache_ttl: int = 90
    compass_cache_ttl: int = 90
    enable_nav_cache: bool = True
    enable_compass_cache: bool = True

    model_config = SettingsConfigDict(env_prefix="CACHE_")
