from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    redis_url: str = "redis://localhost:6379/0"
    nonce_ttl: int = 300
    verification_token_ttl: int = 3600

    model_config = SettingsConfigDict(extra="ignore")
