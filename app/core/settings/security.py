from pydantic_settings import BaseSettings, SettingsConfigDict

class SecuritySettings(BaseSettings):
    min_password_length: int = 3
    secure_password_policy: bool = False

    model_config = SettingsConfigDict(env_prefix="SECURITY_")
