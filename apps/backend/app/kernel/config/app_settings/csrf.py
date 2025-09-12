from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class CsrfSettings(BaseSettings):
    enabled: bool = True
    header_name: str = "X-CSRF-Token"
    cookie_name: str = "XSRF-TOKEN"
    exempt_paths: list[str] | str = Field(
        default_factory=lambda: ["/health", "/readyz", "/metrics", "/ws"]
    )
    require_for_bearer: bool = False

    model_config = SettingsConfigDict(env_prefix="CSRF_")

    @field_validator("exempt_paths", mode="before")
    def split_csv(cls, v):  # noqa: N805
        if not v:
            return cls.model_fields["exempt_paths"].default_factory()
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

