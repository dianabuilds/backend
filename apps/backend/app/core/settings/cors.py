from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class CorsSettings(BaseSettings):
    allowed_origins: List[str] = Field(default_factory=list)
    allow_credentials: bool = True
    allowed_methods: List[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    )
    allowed_headers: List[str] = Field(
        default_factory=lambda: [
            "Authorization",
            "Content-Type",
            "X-CSRF-Token",
            "X-Requested-With",
        ]
    )

    model_config = SettingsConfigDict(env_prefix="CORS_")

    @field_validator("allowed_origins", "allowed_methods", "allowed_headers", mode="before")
    def split_csv(cls, v):
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v
