from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    redis_url: str | None = None
    nonce_ttl: int = 300
    verification_token_ttl: int = 3600

    model_config = SettingsConfigDict(extra="ignore")
