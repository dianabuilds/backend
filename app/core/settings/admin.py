from pydantic_settings import BaseSettings, SettingsConfigDict

class AdminSettings(BaseSettings):
    bootstrap_enabled: bool = True
    username: str = "admin"
    email: str = "admin@example.com"
    password: str = "admin123"

    model_config = SettingsConfigDict(env_prefix="ADMIN_")
