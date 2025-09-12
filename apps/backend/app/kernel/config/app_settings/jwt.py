from pydantic_settings import BaseSettings, SettingsConfigDict


class JwtSettings(BaseSettings):
    secret: str = "test-secret"
    algorithm: str = "HS256"
    audience: str = "backend"
    issuer: str = "app"
    # Access token lifetime (in minutes)
    expires_min: int = 60
    # Refresh token lifetime (in days)
    refresh_expires_days: int = 30
    public_key: str | None = None
    leeway: int = 30

    model_config = SettingsConfigDict(extra="ignore")

    @property
    def expiration(self) -> int:
        return self.expires_min * 60

    @property
    def refresh_expiration(self) -> int:
        return self.refresh_expires_days * 24 * 60 * 60

