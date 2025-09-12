from pydantic import BaseModel, EmailStr
from pydantic_settings import SettingsConfigDict


class SMTPSettings(BaseModel):
    host: str = "localhost"
    port: int = 25
    username: str | None = None
    password: str | None = None
    tls: bool = False
    mail_from: EmailStr = "noreply@example.com"
    mail_from_name: str = "App"
    mock: bool = True

    model_config = SettingsConfigDict(env_prefix="SMTP_")

