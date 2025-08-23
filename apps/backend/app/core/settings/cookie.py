from pydantic_settings import BaseSettings, SettingsConfigDict


class CookieSettings(BaseSettings):
    domain: str = ""
    secure: bool = True
    samesite: str = "strict"

    model_config = SettingsConfigDict(env_prefix="COOKIE_")
