from pydantic_settings import BaseSettings, SettingsConfigDict

class JwtSettings(BaseSettings):
    secret: str = "test-secret"
    algorithm: str = "HS256"
    expiration: int = 60 * 60

    model_config = SettingsConfigDict(env_prefix="JWT_")
