from pydantic_settings import BaseSettings, SettingsConfigDict


class PaymentSettings(BaseSettings):
    jwt_secret: str | None = None
    webhook_secret: str | None = None
    api_base: str = ""

    model_config = SettingsConfigDict(extra="ignore")
