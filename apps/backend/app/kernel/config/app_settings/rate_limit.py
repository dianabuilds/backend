from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RateLimitSettings(BaseSettings):
    enabled: bool = False
    rules_login: str = Field("5/min", alias="RULES_LOGIN")
    rules_login_json: str = Field("5/min", alias="RULES_LOGIN_JSON")
    rules_signup: str = Field("3/hour", alias="RULES_SIGNUP")
    rules_evm_nonce: str = Field("10/min", alias="RULES_EVM_NONCE")
    rules_evm_verify: str = Field("10/min", alias="RULES_EVM_VERIFY")
    rules_change_password: str = Field("5/min", alias="RULES_CHANGE_PASSWORD")

    model_config = SettingsConfigDict(env_prefix="RATE_LIMIT_", extra="ignore")

