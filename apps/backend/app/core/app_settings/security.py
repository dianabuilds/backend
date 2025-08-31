from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecuritySettings(BaseSettings):
    min_password_length: int = 3
    secure_password_policy: bool = False
    admin_roles: list[str] = ["admin", "moderator"]
    allowed_hosts: list[str] = Field(default_factory=list)

    model_config = SettingsConfigDict(env_prefix="SECURITY_")

    @field_validator("allowed_hosts", mode="before")
    def split_csv(cls, v):  # noqa: N805
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v
