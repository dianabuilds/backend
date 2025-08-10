from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class JwtSettings(BaseSettings):
    secret: str = Field("test-secret", alias="JWT_SECRET")
    algorithm: str = Field("HS256", alias="JWT_ALG")
    expires_min: int = Field(60, alias="JWT_EXPIRES_MIN")

    model_config = SettingsConfigDict(extra="ignore")

    @property
    def expiration(self) -> int:
        return self.expires_min * 60
